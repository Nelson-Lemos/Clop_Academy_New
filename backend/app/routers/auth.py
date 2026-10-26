from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_valid_email,
    login_limiter,
    normalize_email,
    validate_password_strength,
)
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import permissions_for
from app.models.messaging import AuditAction
from app.models.user import User, UserRole, UserStatus
from app.schemas.common import MessageOut as MessageOutSchema
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MeOut,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterRequest,
    StudentProfileOut,
    StudentProfileUpdate,
    TokenResponse,
)
from app.services.audit_service import log_audit
from app.services.auth_service import authenticate_user, create_student, get_user_by_email

router = APIRouter(prefix="/auth", tags=["autenticação"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _me_out(user: User) -> MeOut:
    perfil = user.perfil_aluno
    return MeOut(
        id=user.id,
        nome_completo=user.nome_completo,
        email=user.email,
        telefone=user.telefone,
        role=user.role,
        estado=user.estado,
        aceite_termos_em=user.aceite_termos_em,
        email_verificado_em=user.email_verificado_em,
        criado_em=user.created_at,
        perfil_aluno=StudentProfileOut.model_validate(perfil) if perfil else None,
        permissoes=sorted(permissions_for(user.role)),
    )


@router.post("/registo", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def registo(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    request: Request = None,
) -> AuthResponse:
    """Registo público de aluno."""
    email = normalize_email(payload.email)

    if not is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail inválido."
        )

    problemas = validate_password_strength(payload.password)
    if problemas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problemas
        )

    if not payload.aceite_termos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário aceitar os termos e condições para criar a conta.",
        )

    if get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        )

    profile_data = {
        "profissao": payload.profissao,
        "cidade": payload.cidade,
        "provincia": payload.provincia,
        "nivel_educacao": payload.nivel_educacao,
        "objetivo": payload.objetivo,
    }

    user = create_student(
        db,
        nome_completo=payload.nome_completo,
        email=email,
        password=payload.password,
        telefone=payload.telefone,
        aceite_termos=payload.aceite_termos,
        profile_data=profile_data,
    )
    user.aceite_termos_em = _agora()
    log_audit(
        db,
        action=AuditAction.REGISTO,
        user_id=user.id,
        entity="user",
        entity_id=user.id,
        detalhe="Registo público de aluno.",
        request=request,
    )
    db.commit()
    db.refresh(user)

    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=_me_out(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None,
) -> AuthResponse:
    email = normalize_email(payload.email)
    ip = request.client.host if (request and request.client) else "desconhecido"
    chave = f"{ip}:{email}"

    if login_limiter.is_blocked(chave):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Demasiadas tentativas de início de sessão. Aguarde alguns "
                "minutos antes de tentar novamente."
            ),
        )

    user = authenticate_user(db, email, payload.password)
    if user is None:
        login_limiter.register_failure(chave)
        log_audit(
            db,
            action=AuditAction.LOGIN_FALHADO,
            entity="auth",
            detalhe=f"Tentativa falhada de início de sessão para {email}.",
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou palavra-passe inválidos.",
        )

    login_limiter.reset(chave)
    user.ultimo_acesso_em = _agora()
    log_audit(
        db,
        action=AuditAction.LOGIN,
        user_id=user.id,
        entity="auth",
        entity_id=user.id,
        request=request,
    )
    db.commit()

    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=_me_out(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    data = decode_token(payload.refresh_token)
    subject = data.get("sub")

    if not subject or data.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Inicie sessão novamente.",
        )

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida."
        )

    user = db.get(User, user_id)
    if user is None or user.estado != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador não activo."
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=MeOut)
def me(current_user: CurrentUser) -> MeOut:
    return _me_out(current_user)


@router.put("/perfil", response_model=MeOut)
def actualizar_perfil(
    payload: StudentProfileUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    request: Request = None,
) -> MeOut:
    if payload.nome_completo is not None:
        current_user.nome_completo = payload.nome_completo.strip()
    if payload.telefone is not None:
        current_user.telefone = payload.telefone.strip() or None

    perfil = current_user.perfil_aluno
    if perfil is None:
        from app.models.user import StudentProfile

        perfil = StudentProfile(user_id=current_user.id)
        db.add(perfil)

    dados_perfil = payload.model_dump(
        exclude_none=True,
        exclude={"nome_completo", "telefone"},
    )
    for campo, valor in dados_perfil.items():
        setattr(perfil, campo, valor)

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_PERFIL,
        user_id=current_user.id,
        entity="student_profile",
        entity_id=perfil.id,
        request=request,
    )
    db.commit()
    db.refresh(current_user)
    return _me_out(current_user)


@router.post("/password", response_model=MessageOutSchema)
def alterar_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> MessageOutSchema:
    from app.core.security import verify_password

    if not verify_password(payload.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A palavra-passe actual não está correcta.",
        )

    problemas = validate_password_strength(payload.nova_password)
    if problemas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problemas
        )

    current_user.password_hash = hash_password(payload.nova_password)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_PERFIL,
        user_id=current_user.id,
        entity="user",
        entity_id=current_user.id,
        detalhe="Alteração de palavra-passe.",
    )
    db.commit()
    return MessageOutSchema(
        mensagem="Palavra-passe actualizada com sucesso.",
    )
