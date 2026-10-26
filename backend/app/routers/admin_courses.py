from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.utils import PageMeta, PaginatedResponse, page_params, slugify
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import (
    PERM_CURSOS_GERIR,
    PERM_CURSOS_VER,
    PERM_INSCRICOES_GERIR,
    PERM_INSCRICOES_VER,
    PERM_RELATORIOS_VER,
    require_permissions,
)
from app.models.catalog import (
    Cohort,
    Course,
    CourseModule,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonMaterial,
)
from app.models.enrollment import Payment, PaymentStatus
from app.models.messaging import AuditAction
from app.models.user import User
from app.schemas.catalog import (
    CohortCreate,
    CourseAdminOut,
    CourseCreate,
    CourseDetailOut,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    MaterialCreate,
    ModuleCreate,
)
from app.schemas.common import DashboardMetrics, MessageOut
from app.schemas.enrollment import EnrollmentStateUpdate
from app.services.audit_service import log_audit
from app.services.course_service import to_course_detail
from app.services.dashboard_service import metricas

router = APIRouter(prefix="/admin", tags=["administração"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _slug_unico(db: Session, modelo, base: str, campo_slug: str = "slug") -> str:
    slug = slugify(base)
    candidato = slug
    sufixo = 2
    while db.query(modelo).filter(getattr(modelo, campo_slug) == candidato).first():
        candidato = f"{slug}-{sufixo}"
        sufixo += 1
    return candidato


def _obter_curso(db: Session, course_id: int) -> Course:
    curso = db.get(Course, course_id)
    if curso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado."
        )
    return curso


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=DashboardMetrics)
def dashboard_admin(
    current_user: User = Depends(require_permissions(PERM_RELATORIOS_VER)),
    db: Session = Depends(get_db),
) -> DashboardMetrics:
    """Métricas do painel administrativo, obtidas da base de dados."""
    return metricas(db)


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------
@router.get("/cursos", response_model=PaginatedResponse[CourseAdminOut])
def listar_cursos_admin(
    current_user: User = Depends(require_permissions(PERM_CURSOS_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    estado: str | None = Query(default=None, max_length=20),
) -> PaginatedResponse[CourseAdminOut]:
    query = db.query(Course)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(Course.nome.ilike(termo), Course.descricao_resumida.ilike(termo)))
    if estado:
        query = query.filter(Course.estado == estado)

    total = query.count()
    cursos = (
        query.order_by(Course.updated_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    items = []
    for curso in cursos:
        detalhe = to_course_detail(db, curso)
        items.append(
            CourseAdminOut(
                **detalhe.model_dump(),
                criado_em=curso.created_at,
                actualizado_em=curso.updated_at,
            )
        )

    return PaginatedResponse(
        items=items,
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


@router.get("/cursos/{course_id}", response_model=CourseDetailOut)
def detalhe_curso_admin(
    course_id: int,
    current_user: User = Depends(require_permissions(PERM_CURSOS_VER)),
    db: Session = Depends(get_db),
) -> CourseDetailOut:
    return to_course_detail(db, _obter_curso(db, course_id))


@router.post("/cursos", response_model=CourseDetailOut, status_code=status.HTTP_201_CREATED)
def criar_curso(
    payload: CourseCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CourseDetailOut:
    dados = payload.model_dump()
    slug = dados.pop("slug", None) or _slug_unico(db, Course, dados["nome"])
    curso = Course(slug=slug, **dados)
    db.add(curso)
    db.flush()
    log_audit(
        db,
        action=AuditAction.CRIAR_CURSO,
        user_id=current_user.id,
        entity="course",
        entity_id=curso.id,
        detalhe=f"Criação do curso «{curso.nome}».",
        request=request,
    )
    db.commit()
    db.refresh(curso)
    return to_course_detail(db, curso)


@router.put("/cursos/{course_id}", response_model=CourseDetailOut)
def actualizar_curso(
    course_id: int,
    payload: CourseUpdate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CourseDetailOut:
    curso = _obter_curso(db, course_id)
    dados = payload.model_dump(exclude_unset=True)

    if "preco" in dados and dados["preco"] is not None:
        dados["preco"] = max(dados["preco"], 0)

    for campo, valor in dados.items():
        setattr(curso, campo, valor)

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course",
        entity_id=curso.id,
        detalhe="Actualização dos dados do curso.",
        request=request,
    )
    db.commit()
    db.refresh(curso)
    return to_course_detail(db, curso)


@router.post("/cursos/{course_id}/estado", response_model=CourseDetailOut)
def alterar_estado_curso(
    course_id: int,
    estado: str = Query(..., description="DRAFT | PUBLISHED | ARCHIVED"),
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CourseDetailOut:
    if estado not in {CourseStatus.DRAFT, CourseStatus.PUBLISHED, CourseStatus.ARCHIVED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de curso inválido."
        )
    curso = _obter_curso(db, course_id)
    curso.estado = estado
    log_audit(
        db,
        action=AuditAction.PUBLICAR_CURSO
        if estado == CourseStatus.PUBLISHED
        else AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course",
        entity_id=curso.id,
        detalhe=f"Estado do curso alterado para {estado}.",
        request=request,
    )
    db.commit()
    db.refresh(curso)
    return to_course_detail(db, curso)


@router.delete("/cursos/{course_id}", response_model=MessageOut)
def arquivar_curso(
    course_id: int,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    """Arquiva um curso (não apaga: preserva o histórico de inscrições)."""
    curso = _obter_curso(db, course_id)
    curso.estado = CourseStatus.ARCHIVED
    curso.inscricoes_abertas = False
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course",
        entity_id=curso.id,
        detalhe="Curso arquivado.",
        request=request,
    )
    db.commit()
    return MessageOut(
        mensagem="Curso arquivado.",
        detalhe="O curso deixa de estar visível no portal, mantendo o histórico.",
    )


# ---------------------------------------------------------------------------
# Módulos e aulas
# ---------------------------------------------------------------------------
@router.post("/cursos/{course_id}/modulos", status_code=status.HTTP_201_CREATED)
def criar_modulo(
    course_id: int,
    payload: ModuleCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    curso = _obter_curso(db, course_id)
    modulo = CourseModule(
        curso_id=curso.id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        ordem=payload.ordem,
    )
    db.add(modulo)
    db.flush()

    for aula in payload.aulas:
        db.add(Lesson(modulo_id=modulo.id, **aula.model_dump()))

    curso.numero_aulas = sum(len(m.aulas) for m in curso.modulos) + len(payload.aulas)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course_module",
        entity_id=modulo.id,
        detalhe=f"Criação do módulo «{modulo.titulo}».",
        request=request,
    )
    db.commit()
    db.refresh(modulo)
    return {"id": modulo.id, "titulo": modulo.titulo}


@router.put("/modulos/{module_id}")
def actualizar_modulo(
    module_id: int,
    payload: ModuleCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    modulo = db.get(CourseModule, module_id)
    if modulo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado."
        )
    modulo.titulo = payload.titulo
    modulo.descricao = payload.descricao
    modulo.ordem = payload.ordem
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course_module",
        entity_id=modulo.id,
        request=request,
    )
    db.commit()
    return {"id": modulo.id, "titulo": modulo.titulo}


@router.delete("/modulos/{module_id}", response_model=MessageOut)
def eliminar_modulo(
    module_id: int,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    modulo = db.get(CourseModule, module_id)
    if modulo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado."
        )
    curso_id = modulo.curso_id
    db.delete(modulo)
    db.flush()
    curso = db.get(Course, curso_id)
    if curso is not None:
        curso.numero_aulas = sum(len(m.aulas) for m in curso.modulos)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="course_module",
        entity_id=module_id,
        detalhe="Remoção de módulo.",
        request=request,
    )
    db.commit()
    return MessageOut(mensagem="Módulo removido.")


@router.post("/modulos/{module_id}/aulas", status_code=status.HTTP_201_CREATED)
def criar_aula(
    module_id: int,
    payload: LessonCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    modulo = db.get(CourseModule, module_id)
    if modulo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Módulo não encontrado."
        )
    aula = Lesson(modulo_id=modulo.id, **payload.model_dump())
    db.add(aula)
    db.flush()
    curso = db.get(Course, modulo.curso_id)
    if curso is not None:
        curso.numero_aulas = sum(len(m.aulas) for m in curso.modulos)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="lesson",
        entity_id=aula.id,
        detalhe=f"Criação da aula «{aula.titulo}».",
        request=request,
    )
    db.commit()
    db.refresh(aula)
    return {"id": aula.id, "titulo": aula.titulo}


@router.put("/aulas/{lesson_id}")
def actualizar_aula(
    lesson_id: int,
    payload: LessonUpdate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    aula = db.get(Lesson, lesson_id)
    if aula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada."
        )
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(aula, campo, valor)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="lesson",
        entity_id=aula.id,
        request=request,
    )
    db.commit()
    return {"id": aula.id, "titulo": aula.titulo}


@router.delete("/aulas/{lesson_id}", response_model=MessageOut)
def eliminar_aula(
    lesson_id: int,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    aula = db.get(Lesson, lesson_id)
    if aula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada."
        )
    curso_id = aula.modulo.curso_id if aula.modulo else None
    db.delete(aula)
    db.flush()
    if curso_id:
        curso = db.get(Course, curso_id)
        if curso is not None:
            curso.numero_aulas = sum(len(m.aulas) for m in curso.modulos)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="lesson",
        entity_id=lesson_id,
        detalhe="Remoção de aula.",
        request=request,
    )
    db.commit()
    return MessageOut(mensagem="Aula removida.")


@router.post("/aulas/{lesson_id}/materiais", status_code=status.HTTP_201_CREATED)
def adicionar_material(
    lesson_id: int,
    payload: MaterialCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    aula = db.get(Lesson, lesson_id)
    if aula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada."
        )
    material = LessonMaterial(aula_id=aula.id, **payload.model_dump())
    db.add(material)
    db.flush()
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="lesson_material",
        entity_id=material.id,
        request=request,
    )
    db.commit()
    return {"id": material.id, "titulo": material.titulo}


@router.delete("/materiais/{material_id}", response_model=MessageOut)
def eliminar_material(
    material_id: int,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
) -> MessageOut:
    material = db.get(LessonMaterial, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado."
        )
    db.delete(material)
    db.commit()
    return MessageOut(mensagem="Material removido.")


# ---------------------------------------------------------------------------
# Turmas
# ---------------------------------------------------------------------------
@router.post("/cursos/{course_id}/turmas", status_code=status.HTTP_201_CREATED)
def criar_turma(
    course_id: int,
    payload: CohortCreate,
    current_user: User = Depends(require_permissions(PERM_CURSOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    curso = _obter_curso(db, course_id)
    turma = Cohort(curso_id=curso.id, **payload.model_dump())
    db.add(turma)
    db.flush()
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CURSO,
        user_id=current_user.id,
        entity="cohort",
        entity_id=turma.id,
        detalhe=f"Criação da turma «{turma.nome}».",
        request=request,
    )
    db.commit()
    return {"id": turma.id, "nome": turma.nome}


# ---------------------------------------------------------------------------
# Inscrições
# ---------------------------------------------------------------------------
@router.get("/inscricoes")
def listar_inscricoes_admin(
    current_user: User = Depends(require_permissions(PERM_INSCRICOES_VER)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    estado: str | None = Query(default=None, max_length=20),
    curso_id: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
) -> dict:
    query = db.query(Enrollment).join(User, Enrollment.user_id == User.id)
    if estado:
        query = query.filter(Enrollment.estado == estado)
    if curso_id:
        query = query.filter(Enrollment.course_id == curso_id)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(
            or_(User.nome_completo.ilike(termo), User.email.ilike(termo))
        )

    total = query.count()
    inscricoes = (
        query.order_by(Enrollment.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": i.id,
                "aluno_id": i.user_id,
                "aluno_nome": i.user.nome_completo,
                "aluno_email": i.user.email,
                "course_id": i.course_id,
                "curso_nome": i.curso.nome,
                "estado": i.estado,
                "percentagem_progresso": i.percentagem_progresso,
                "preco_pago": str(i.preco_pago),
                "criado_em": i.created_at,
            }
            for i in inscricoes
        ],
        "meta": PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ).model_dump(),
    }


@router.post("/inscricoes/{enrollment_id}/estado")
def alterar_estado_inscricao(
    enrollment_id: int,
    payload: EnrollmentStateUpdate,
    current_user: User = Depends(require_permissions(PERM_INSCRICOES_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> dict:
    inscricao = db.get(Enrollment, enrollment_id)
    if inscricao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada."
        )
    estados_validos = {e for e in vars(EnrollmentStatus).values() if isinstance(e, str)}
    if payload.estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de inscrição inválido."
        )

    inscricao.estado = payload.estado
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_ESTADO_INSCRICAO,
        user_id=current_user.id,
        entity="enrollment",
        entity_id=inscricao.id,
        detalhe=f"Estado alterado para {payload.estado}. {payload.motivo or ''}".strip(),
        request=request,
    )
    db.commit()
    return {"id": inscricao.id, "estado": inscricao.estado}
