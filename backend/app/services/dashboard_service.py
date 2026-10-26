from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.catalog import Course, CourseStatus, Enrollment, EnrollmentStatus
from app.models.content import Article, ArticleStatus, Event, EventStatus
from app.models.enrollment import Payment, PaymentStatus
from app.models.market import Certificate
from app.models.messaging import ContactMessage, ContactMessageStatus
from app.models.user import User, UserRole
from app.schemas.common import DashboardMetrics


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def metricas(db: Session) -> DashboardMetrics:
    """Métricas do painel administrativo, obtidas da base de dados."""
    agora = _agora()

    alunos = db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0

    inscricoes_por_curso = [
        {
            "curso_id": row.course_id,
            "curso": row.nome,
            "total": row.total,
        }
        for row in db.query(
            Enrollment.course_id.label("course_id"),
            Course.nome.label("nome"),
            func.count(Enrollment.id).label("total"),
        )
        .join(Course, Course.id == Enrollment.course_id)
        .group_by(Enrollment.course_id, Course.nome)
        .order_by(func.count(Enrollment.id).desc())
        .all()
    ]

    cursos_activos = (
        db.query(func.count(Course.id))
        .filter(Course.estado == CourseStatus.PUBLISHED)
        .scalar()
        or 0
    )
    cursos_publicados = cursos_activos
    cursos_total = db.query(func.count(Course.id)).scalar() or 0

    pagamentos_pendentes = (
        db.query(func.count(Payment.id))
        .filter(Payment.estado.in_([PaymentStatus.PENDENTE, PaymentStatus.EM_PROCESSAMENTO]))
        .scalar()
        or 0
    )
    pagamentos_confirmados = (
        db.query(func.count(Payment.id))
        .filter(Payment.estado == PaymentStatus.CONFIRMADO)
        .scalar()
        or 0
    )

    total_inscricoes = db.query(func.count(Enrollment.id)).scalar() or 0
    inscricoes_activas = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.estado == EnrollmentStatus.ACTIVA)
        .scalar()
        or 0
    )

    artigos_publicados = (
        db.query(func.count(Article.id))
        .filter(Article.estado == ArticleStatus.PUBLICADO)
        .scalar()
        or 0
    )
    eventos_publicados = (
        db.query(func.count(Event.id))
        .filter(Event.estado == EventStatus.PUBLICADO)
        .scalar()
        or 0
    )
    eventos_proximos = (
        db.query(func.count(Event.id))
        .filter(Event.estado == EventStatus.PUBLICADO, Event.inicio >= agora)
        .scalar()
        or 0
    )
    pedidos_contacto = (
        db.query(func.count(ContactMessage.id))
        .filter(ContactMessage.estado.in_(
            [ContactMessageStatus.NOVO, ContactMessageStatus.EM_ANALISE]
        ))
        .scalar()
        or 0
    )
    certificados_emitidos = db.query(func.count(Certificate.id)).scalar() or 0

    return DashboardMetrics(
        alunos_registados=alunos,
        inscricoes_por_curso=inscricoes_por_curso,
        cursos_activos=cursos_activos,
        cursos_publicados=cursos_publicados,
        pagamentos_pendentes=pagamentos_pendentes,
        pagamentos_confirmados=pagamentos_confirmados,
        total_inscricoes=total_inscricoes,
        inscricoes_activas=inscricoes_activas,
        artigos_publicados=artigos_publicados,
        eventos_publicados=eventos_publicados,
        eventos_proximos=eventos_proximos,
        pedidos_contacto=pedidos_contacto,
        certificados_emitidos=certificados_emitidos,
        avaliacoes_pendentes=0,
    )


def dashboard_aluno(db: Session, user_id: int) -> dict:
    """Indicadores da área do aluno."""
    inscricoes = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id)
        .order_by(Enrollment.updated_at.desc())
        .all()
    )

    ativas = [i for i in inscricoes if i.estado == EnrollmentStatus.ACTIVA]
    concluidas = [i for i in inscricoes if i.estado == EnrollmentStatus.CONCLUIDA]

    agora = _agora()
    proximos = (
        db.query(Event)
        .filter(Event.estado == EventStatus.PUBLICADO, Event.inicio >= agora)
        .order_by(Event.inicio)
        .limit(5)
        .all()
    )

    return {
        "total_inscricoes": len(inscricoes),
        "inscricoes_ativas": len(ativas),
        "inscricoes_concluidas": len(concluidas),
        "progresso_medio": (
            int(sum(i.percentagem_progresso for i in ativas) / len(ativas)) if ativas else 0
        ),
        "proximos_eventos": len(proximos),
    }
