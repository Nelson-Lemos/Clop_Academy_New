from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.security import hash_password
from app.core.utils import PageMeta, PaginatedResponse, page_params
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import (
    PERM_AUDITORIA_VER,
    PERM_MERCADOS_GERIR,
    PERM_PAGAMENTOS_GERIR,
    PERM_PAGAMENTOS_VER,
    PERM_UTILIZADORES_GERIR,
    require_permissions,
    require_superadmin,
)
from app.models.catalog import Course, Enrollment
from app.models.enrollment import Payment, PaymentStatus
from app.models.market import (
    EconomicEvent,
    MacroIndicator,
    MarketInstrument,
    MarketQuote,
    QuoteFreshness,
)
from app.models.messaging import AuditAction, AuditLog, ContactMessage
from app.models.user import InstructorProfile, User, UserRole, UserStatus
from app.schemas.common import (
    AuditLogOut,
    ContactMessageOut,
    ContactMessageUpdate,
    MessageOut,
)
from app.schemas.enrollment import PaymentAdminOut, PaymentConfirm
from app.schemas.market import (
    EconomicEventCreate,
    EconomicEventOut,
    IndicatorCreate,
    InstrumentOut,
    MacroIndicatorOut,
    QuoteCreate,
    QuoteOut,
)
from app.services import market_service
from app.services.audit_service import log_audit
from app.services.enrollment_service import confirmar_pagamento

router = APIRouter(prefix="/admin", tags=["administração — operações"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Utilizadores
# ---------------------------------------------------------------------------
@router.get("/utilizadores")
def listar_utilizadores(
    current_user: User = Depends(require_permissions(PERM_UTILIZADORES_GERIR)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    role: str | None = Query(default=None, max_length=20),
) -> dict:
    query = db.query(User)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(User.nome_completo.ilike(termo), User.email.ilike(termo)))
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    utilizadores = (
        query.order_by(User.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": u.id,
                "nome_completo": u.nome_completo,
                "email": u.email,
                "telefone": u.telefone,
                "role": u.role,
                "estado": u.estado,
                "criado_em": u.created_at,
                "ultimo_acesso_em": u.ultimo_acesso_em,
            }
            for u in utilizadores
        ],
        "meta": PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ).model_dump(),
    }


@router.post("/utilizadores", status_code=status.HTTP_201_CREATED)
def criar_utilizador(
    payload: dict,
    current_user: User = Depends(require_permissions(PERM_UTILIZADORES_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    """Cria um utilizador (formador, editor, financeiro, admin)."""
    nome = str(payload.get("nome_completo", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", UserRole.INSTRUCTOR)).upper()

    if len(nome) < 3 or not email or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome, e-mail e palavra-passe (mínimo 8 caracteres) são obrigatórios.",
        )
    if role not in {
        UserRole.STUDENT,
        UserRole.INSTRUCTOR,
        UserRole.EDITOR,
        UserRole.FINANCE,
        UserRole.ADMIN,
        UserRole.SUPERADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Função inválida."
        )
    if role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas um super administrador pode criar outros super administradores.",
        )
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um utilizador com este e-mail.",
        )

    user = User(
        nome_completo=nome,
        email=email,
        password_hash=hash_password(password),
        role=role,
        telefone=payload.get("telefone"),
        estado=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()

    if role == UserRole.INSTRUCTOR:
        db.add(
            InstructorProfile(
                user_id=user.id,
                cargo=payload.get("cargo"),
                bio=payload.get("bio"),
            )
        )

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_UTILIZADOR,
        user_id=current_user.id,
        entity="user",
        entity_id=user.id,
        detalhe=f"Criação de utilizador com a função {role}.",
        request=request,
    )
    db.commit()
    return {"id": user.id, "nome_completo": user.nome_completo, "role": user.role}


@router.patch("/utilizadores/{user_id}/estado")
def alterar_estado_utilizador(
    user_id: int,
    estado: str = Query(..., description="ACTIVE | INACTIVE | SUSPENDED"),
    current_user: User = Depends(require_permissions(PERM_UTILIZADORES_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    if estado not in {UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Estado inválido."
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado."
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não pode alterar o estado da sua própria conta.",
        )

    user.estado = estado
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_UTILIZADOR,
        user_id=current_user.id,
        entity="user",
        entity_id=user.id,
        detalhe=f"Estado do utilizador alterado para {estado}.",
        request=request,
    )
    db.commit()
    return {"id": user.id, "estado": user.estado}


@router.patch("/utilizadores/{user_id}/funcao")
def alterar_funcao_utilizador(
    user_id: int,
    role: str = Query(...),
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    if role not in {
        UserRole.STUDENT,
        UserRole.INSTRUCTOR,
        UserRole.EDITOR,
        UserRole.FINANCE,
        UserRole.ADMIN,
        UserRole.SUPERADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Função inválida."
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado."
        )
    anterior = user.role
    user.role = role
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_PERMISSOES,
        user_id=current_user.id,
        entity="user",
        entity_id=user.id,
        detalhe=f"Função alterada de {anterior} para {role}.",
        request=request,
    )
    db.commit()
    return {"id": user.id, "role": user.role, "anterior": anterior}


# ---------------------------------------------------------------------------
# Pagamentos
# ---------------------------------------------------------------------------
@router.get("/pagamentos", response_model=PaginatedResponse[PaymentAdminOut])
def listar_pagamentos(
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    estado: str | None = Query(default=None, max_length=20),
    q: str | None = Query(default=None, max_length=120),
) -> PaginatedResponse[PaymentAdminOut]:
    query = db.query(Payment).join(User, Payment.user_id == User.id)
    if estado:
        query = query.filter(Payment.estado == estado)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(User.nome_completo.ilike(termo), Payment.referencia.ilike(termo)))

    total = query.count()
    pagamentos = (
        query.order_by(Payment.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    items = []
    for pagamento in pagamentos:
        item = PaymentAdminOut.model_validate(pagamento)
        item.aluno_nome = pagamento.user.nome_completo if pagamento.user else None
        item.aluno_email = pagamento.user.email if pagamento.user else None
        item.curso_nome = pagamento.curso.nome if pagamento.curso else None
        item.comprovativos = len(pagamento.comprovativos)
        items.append(item)

    return PaginatedResponse(
        items=items,
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


@router.post("/pagamentos/{payment_id}/confirmar", response_model=PaymentAdminOut)
def confirmar_pagamento_admin(
    payment_id: int,
    payload: PaymentConfirm,
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> PaymentAdminOut:
    """Confirma (ou recusa) um pagamento após validação do comprovativo."""
    pagamento = db.get(Payment, payment_id)
    if pagamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pagamento não encontrado."
        )
    if pagamento.estado == PaymentStatus.CONFIRMADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pagamento já se encontra confirmado.",
        )

    if payload.estado == PaymentStatus.CONFIRMADO:
        confirmar_pagamento(db, pagamento, current_user.id)
    elif payload.estado in {PaymentStatus.RECUSADO, PaymentStatus.CANCELADO}:
        pagamento.estado = payload.estado
        pagamento.confirmado_por = current_user.id
        pagamento.confirmado_em = _agora()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de pagamento inválido."
        )

    if payload.notas:
        pagamento.notas = payload.notas

    log_audit(
        db,
        action=(
            AuditAction.CONFIRMAR_PAGAMENTO
            if pagamento.estado == PaymentStatus.CONFIRMADO
            else AuditAction.RECUSAR_PAGAMENTO
        ),
        user_id=current_user.id,
        entity="payment",
        entity_id=pagamento.id,
        detalhe=(
            f"Pagamento {pagamento.referencia} → {pagamento.estado}. "
            f"{payload.notas or ''}".strip()
        ),
        request=request,
    )
    db.commit()
    db.refresh(pagamento)

    item = PaymentAdminOut.model_validate(pagamento)
    item.aluno_nome = pagamento.user.nome_completo if pagamento.user else None
    item.aluno_email = pagamento.user.email if pagamento.user else None
    item.curso_nome = pagamento.curso.nome if pagamento.curso else None
    item.comprovativos = len(pagamento.comprovativos)
    return item


# ---------------------------------------------------------------------------
# Avaliações (correcção)
# ---------------------------------------------------------------------------
@router.get("/avaliacoes/submissoes")
def listar_submissoes(
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    avaliacao_id: int | None = Query(default=None),
) -> dict:
    from app.models.enrollment import Submission

    query = db.query(Submission)
    if avaliacao_id:
        query = query.filter(Submission.assessment_id == avaliacao_id)

    total = query.count()
    submissoes = (
        query.order_by(Submission.submetida_em.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": s.id,
                "assessment_id": s.assessment_id,
                "avaliacao": s.avaliacao.titulo if s.avaliacao else None,
                "user_id": s.user_id,
                "aluno": s.user.nome_completo if s.user else None,
                "tentativa": s.tentativa,
                "estado": s.estado,
                "nota": s.nota,
                "submetida_em": s.submetida_em,
            }
            for s in submissoes
        ],
        "meta": PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ).model_dump(),
    }


# ---------------------------------------------------------------------------
# Contactos
# ---------------------------------------------------------------------------
@router.get("/contactos", response_model=PaginatedResponse[ContactMessageOut])
def listar_contactos(
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    estado: str | None = Query(default=None, max_length=20),
) -> PaginatedResponse[ContactMessageOut]:
    query = db.query(ContactMessage)
    if estado:
        query = query.filter(ContactMessage.estado == estado)

    total = query.count()
    mensagens = (
        query.order_by(ContactMessage.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return PaginatedResponse(
        items=[ContactMessageOut.model_validate(m) for m in mensagens],
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


@router.patch("/contactos/{message_id}", response_model=ContactMessageOut)
def actualizar_contacto(
    message_id: int,
    payload: ContactMessageUpdate,
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_VER)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ContactMessageOut:
    mensagem = db.get(ContactMessage, message_id)
    if mensagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )
    mensagem.estado = payload.estado
    if payload.estado == "RESPONDIDO":
        mensagem.respondido_por = current_user.id
        mensagem.respondido_em = _agora()
    log_audit(
        db,
        action=AuditAction.CONTACTO_RECEBIDO,
        user_id=current_user.id,
        entity="contact_message",
        entity_id=mensagem.id,
        detalhe=f"Estado do pedido alterado para {payload.estado}.",
        request=request,
    )
    db.commit()
    db.refresh(mensagem)
    return ContactMessageOut.model_validate(mensagem)


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------
@router.get("/auditoria", response_model=PaginatedResponse[AuditLogOut])
def listar_auditoria(
    current_user: User = Depends(require_permissions(PERM_AUDITORIA_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    action: str | None = Query(default=None, max_length=50),
    entity: str | None = Query(default=None, max_length=50),
) -> PaginatedResponse[AuditLogOut]:
    query = db.query(AuditLog).outerjoin(User, AuditLog.user_id == User.id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity:
        query = query.filter(AuditLog.entity == entity)

    total = query.count()
    registos = (
        query.order_by(AuditLog.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    items = []
    for registo in registos:
        item = AuditLogOut.model_validate(registo)
        item.utilizador_nome = registo.user.nome_completo if registo.user else None
        items.append(item)

    return PaginatedResponse(
        items=items,
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


# ---------------------------------------------------------------------------
# Dados de mercado
# ---------------------------------------------------------------------------
@router.get("/mercados/fontes")
def fontes(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
) -> dict:
    return {
        "fontes": [f.model_dump(mode="json") for f in market_service.status_fontes()]
    }


@router.post("/mercados/sincronizar")
def sincronizar(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    """Consulta as fontes configuradas e actualiza a base de dados."""
    resultados = market_service.sincronizar_fontes(db)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_DADOS_MERCADO,
        user_id=current_user.id,
        entity="market",
        detalhe=f"Sincronização de {len(resultados)} fonte(s).",
        request=request,
    )
    db.commit()
    return {
        "resultados": [
            {
                "ok": r.ok,
                "mensagem": r.mensagem,
                "cotacoes": len(r.quotes),
                "consultado_em": r.consultado_em.isoformat(),
            }
            for r in resultados
        ]
    }


@router.get("/mercados/cotacoes", response_model=list[QuoteOut])
def listar_cotacoes(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
    mercado: str | None = Query(default=None, max_length=20),
) -> list[QuoteOut]:
    query = db.query(MarketQuote)
    if mercado:
        query = query.filter(MarketQuote.mercado == mercado)
    cotacoes = query.order_by(MarketQuote.mercado, MarketQuote.nome).all()
    return [QuoteOut.model_validate(c) for c in cotacoes]


@router.post("/mercados/cotacoes", response_model=QuoteOut, status_code=status.HTTP_201_CREATED)
def registar_cotacao(
    payload: QuoteCreate,
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> QuoteOut:
    """Regista uma cotação com origem e data explícitas (dados históricos/manuais)."""
    dados = payload.model_dump()
    instrument_id = dados.pop("instrument_id", None)

    registo = (
        db.query(MarketQuote)
        .filter(
            MarketQuote.simbolo == dados["simbolo"],
            MarketQuote.fonte == dados["fonte"],
        )
        .first()
    )
    if registo is None:
        registo = MarketQuote(**dados)
        db.add(registo)
    else:
        for campo, valor in dados.items():
            setattr(registo, campo, valor)

    registo.consultado_em = _agora()

    if instrument_id:
        instrumento = db.get(MarketInstrument, instrument_id)
        if instrumento is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrumento não encontrado.",
            )
        registo.mercado = instrumento.mercado
        registo.tipo = instrumento.tipo

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_DADOS_MERCADO,
        user_id=current_user.id,
        entity="market_quote",
        entity_id=registo.id,
        detalhe=f"Cotação {registo.simbolo} ({registo.fonte}).",
        request=request,
    )
    db.commit()
    db.refresh(registo)
    return QuoteOut.model_validate(registo)


@router.get("/mercados/instrumentos", response_model=list[InstrumentOut])
def listar_instrumentos(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
) -> list[InstrumentOut]:
    instrumentos = db.query(MarketInstrument).order_by(MarketInstrument.nome).all()
    return [InstrumentOut.model_validate(i) for i in instrumentos]


@router.get("/mercados/indicadores", response_model=list[MacroIndicatorOut])
def listar_indicadores(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
) -> list[MacroIndicatorOut]:
    indicadores = db.query(MacroIndicator).order_by(MacroIndicator.nome).all()
    return [MacroIndicatorOut.model_validate(i) for i in indicadores]


@router.post("/mercados/indicadores", response_model=MacroIndicatorOut, status_code=status.HTTP_201_CREATED)
def registar_indicador(
    payload: IndicatorCreate,
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MacroIndicatorOut:
    dados = payload.model_dump()
    registo = db.query(MacroIndicator).filter(MacroIndicator.codigo == dados["codigo"]).first()
    if registo is None:
        registo = MacroIndicator(**dados)
        db.add(registo)
    else:
        for campo, valor in dados.items():
            setattr(registo, campo, valor)
    registo.consultado_em = _agora()
    registo.atualizado_em = _agora()

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_DADOS_MERCADO,
        user_id=current_user.id,
        entity="macro_indicator",
        entity_id=registo.id,
        detalhe=f"Indicador {registo.codigo} ({registo.fonte}).",
        request=request,
    )
    db.commit()
    db.refresh(registo)
    return MacroIndicatorOut.model_validate(registo)


@router.get("/mercados/calendario", response_model=list[EconomicEventOut])
def listar_calendario(
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
) -> list[EconomicEventOut]:
    eventos = (
        db.query(EconomicEvent).order_by(EconomicEvent.data).limit(200).all()
    )
    return [EconomicEventOut.model_validate(e) for e in eventos]


@router.post("/mercados/calendario", response_model=EconomicEventOut, status_code=status.HTTP_201_CREATED)
def registar_evento_economico(
    payload: EconomicEventCreate,
    current_user: User = Depends(require_permissions(PERM_MERCADOS_GERIR)),
    db: Session = Depends(get_db),
) -> EconomicEventOut:
    evento = EconomicEvent(**payload.model_dump())
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return EconomicEventOut.model_validate(evento)


# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------
@router.get("/relatorios/inscricoes")
def relatorio_inscricoes(
    current_user: User = Depends(require_permissions(PERM_PAGAMENTOS_VER)),
    db: Session = Depends(get_db),
) -> dict:
    """Relatório de inscrições e receita confirmada (valores da base de dados)."""
    linhas = (
        db.query(
            Course.nome.label("curso"),
            Course.id.label("course_id"),
        )
        .distinct()
        .all()
    )

    resultado = []
    for linha in linhas:
        inscricoes = (
            db.query(Enrollment)
            .filter(Enrollment.course_id == linha.course_id)
            .count()
        )
        activas = (
            db.query(Enrollment)
            .filter(
                Enrollment.course_id == linha.course_id,
                Enrollment.estado == "ACTIVA",
            )
            .count()
        )
        receita = (
            db.query(Payment)
            .filter(
                Payment.course_id == linha.course_id,
                Payment.estado == PaymentStatus.CONFIRMADO,
            )
            .sum(Payment.valor)
            or 0
        )
        resultado.append(
            {
                "curso_id": linha.course_id,
                "curso": linha.curso,
                "inscricoes": inscricoes,
                "inscricoes_ativas": activas,
                "receita_confirmada": str(receita),
            }
        )

    return {"itens": resultado}
