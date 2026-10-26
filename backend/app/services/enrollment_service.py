from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import generate_public_code
from app.models.catalog import (
    Course,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    ProgressRecord,
)
from app.models.enrollment import (
    Assessment,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Submission,
)
from app.models.messaging import NotificationType
from app.models.user import User
from app.services.notification_service import notify


def curso_pode_inscrever(curso: Course) -> tuple[bool, str | None]:
    """Verifica as condições de inscrição de um curso (regras no backend)."""
    if curso.estado != "PUBLISHED":
        return False, "Este curso não está disponível para inscrição."
    if not curso.inscricoes_abertas:
        return False, "As inscrições para este curso estão encerradas."
    return True, None


def contar_inscricoes(db: Session, course_id: int) -> int:
    return (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.estado.in_(
                [
                    EnrollmentStatus.ACTIVA,
                    EnrollmentStatus.CONCLUIDA,
                    EnrollmentStatus.AGUARDA_PAGAMENTO,
                    EnrollmentStatus.PENDENTE,
                ]
            ),
        )
        .count()
    )


def inscricao_existente(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )


def total_aulas(curso: Course) -> int:
    return sum(len(modulo.aulas) for modulo in curso.modulos)


def aulas_do_curso(curso: Course) -> list[Lesson]:
    aulas: list[Lesson] = []
    for modulo in curso.modulos:
        aulas.extend(modulo.aulas)
    return aulas


def recalcular_progresso(db: Session, inscricao: Enrollment) -> int:
    """Recalcula a percentagem de progresso a partir das aulas concluídas."""
    curso = inscricao.curso
    aulas = aulas_do_curso(curso)
    if not aulas:
        inscricao.percentagem_progresso = 0
        return 0

    concluidas = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.enrollment_id == inscricao.id,
            ProgressRecord.concludida.is_(True),
        )
        .count()
    )
    percentagem = int(round(concluidas / len(aulas) * 100))
    inscricao.percentagem_progresso = min(100, percentagem)
    return inscricao.percentagem_progresso


def marcar_aula_concluida(
    db: Session, inscricao: Enrollment, lesson_id: int, *, percentagem_video: int = 100
) -> ProgressRecord:
    """Regista a conclusão de uma aula (idempotente)."""
    aula = db.get(Lesson, lesson_id)
    if aula is None:
        raise ValueError("Aula inexistente.")

    modulo = aula.modulo
    if modulo is None or modulo.curso_id != inscricao.course_id:
        raise ValueError("Aula não pertence ao curso desta inscrição.")

    registo = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.enrollment_id == inscricao.id,
            ProgressRecord.lesson_id == lesson_id,
        )
        .first()
    )

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    if registo is None:
        registo = ProgressRecord(
            enrollment_id=inscricao.id,
            lesson_id=lesson_id,
            concludida=True,
            percentagem_video=percentagem_video,
            completed_at=agora,
        )
        db.add(registo)
    else:
        registo.concludida = True
        registo.percentagem_video = percentagem_video
        registo.completed_at = registo.completed_at or agora

    if inscricao.iniciado_em is None:
        inscricao.iniciado_em = agora

    recalcular_progresso(db, inscricao)

    # Conclusão automática da inscrição quando a percentagem mínima é atingida.
    if (
        inscricao.estado == EnrollmentStatus.ACTIVA
        and inscricao.percentagem_progresso >= curso.percentagem_conclusao_minima
    ):
        inscricao.estado = EnrollmentStatus.CONCLUIDA
        inscricao.concluido_em = agora

    db.flush()
    return registo


def aluno_tem_acesso(inscricao: Enrollment) -> bool:
    """Acesso ao conteúdo exige inscrição activa ou concluída."""
    return inscricao.estado in {EnrollmentStatus.ACTIVA, EnrollmentStatus.CONCLUIDA}


def avaliacoes_pendentes(db: Session, inscricao: Enrollment) -> int:
    """Conta avaliações por submeter para a inscrição dada."""
    curso_id = inscricao.course_id
    avaliacoes = (
        db.query(Assessment)
        .filter(Assessment.course_id == curso_id, Assessment.published.is_(True))
        .all()
    )
    if not avaliacoes:
        return 0

    submissoes = {
        (s.assessment_id, s.tentativa)
        for s in db.query(Submission)
        .filter(Submission.enrollment_id == inscricao.id)
        .all()
    }

    pendentes = 0
    for avaliacao in avaliacoes:
        feitas = sum(1 for a_id, _ in submissoes if a_id == avaliacao.id)
        if feitas < avaliacao.tentativas_maximas:
            pendentes += 1
    return pendentes


def requisitos_certificado(inscricao: Enrollment) -> tuple[bool, str | None]:
    """Verifica se o aluno cumpre os requisitos de conclusão do curso."""
    curso = inscricao.curso
    aulas = aulas_do_curso(curso)

    if not aulas:
        return False, "O curso ainda não tem aulas publicadas."

    obrigatorias = [a for a in aulas if a.obrigatoria]
    if len(obrigatorias) < curso.aulas_obrigatorias_minimas:
        return False, "O curso ainda não cumpre o número mínimo de aulas obrigatórias."

    concluidas = (
        inscricao.percentagem_progresso >= curso.percentagem_conclusao_minima
    )
    if not concluidas:
        return (
            False,
            f"Progresso insuficiente ({inscricao.percentagem_progresso}% de "
            f"{curso.percentagem_conclusao_minima}% exigidos).",
        )

    avaliacoes = (
        db.query(Assessment)
        .filter(Assessment.course_id == curso.id, Assessment.published.is_(True))
        .all()
    )
    for avaliacao in avaliacoes:
        melhor = (
            db.query(Submission)
            .filter(
                Submission.enrollment_id == inscricao.id,
                Submission.assessment_id == avaliacao.id,
            )
            .order_by(Submission.nota.desc())
            .first()
        )
        if melhor is None:
            return False, f"Avaliação pendente: {avaliacao.titulo}."
        if melhor.nota is not None and melhor.nota < avaliacao.nota_aprovacao:
            return False, f"Nota mínima não atingida em: {avaliacao.titulo}."

    return True, None


def criar_pagamento(
    db: Session,
    *,
    inscricao: Enrollment,
    user: User,
    metodo: str = PaymentMethod.MANUAL,
    notas: str | None = None,
) -> Payment:
    """Cria um registo de pagamento pendente.

    O valor é copiado do preço do curso no servidor — nunca de um valor
    enviado pelo cliente.
    """
    curso = inscricao.curso
    referencia = generate_public_code("CLOP-", 10)

    pagamento = Payment(
        enrollment_id=inscricao.id,
        user_id=user.id,
        course_id=curso.id,
        referencia=referencia,
        valor=curso.preco,
        moeda=curso.moeda,
        metodo=metodo,
        estado=PaymentStatus.PENDENTE,
        notas=notas,
    )
    db.add(pagamento)
    db.flush()
    return pagamento


def confirmar_pagamento(db: Session, pagamento: Payment, admin_id: int) -> Payment:
    """Confirma um pagamento e activa a inscrição correspondente."""
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    pagamento.estado = PaymentStatus.CONFIRMADO
    pagamento.confirmado_por = admin_id
    pagamento.confirmado_em = agora

    inscricao = db.get(Enrollment, pagamento.enrollment_id)
    if inscricao is not None:
        inscricao.estado = EnrollmentStatus.ACTIVA
        if inscricao.iniciado_em is None:
            inscricao.iniciado_em = agora
        inscricao.preco_pago = pagamento.valor

        notify(
            db,
            user_id=inscricao.user_id,
            titulo="Pagamento confirmado",
            mensagem=(
                f"A tua inscrição em «{inscricao.curso.nome}» foi confirmada. "
                "Já tens acesso ao conteúdo do curso."
            ),
            tipo=NotificationType.PAGAMENTO,
            ligacao=f"/aluno/cursos/{inscricao.course_id}",
        )
    return pagamento


def dados_certificado(inscricao: Enrollment) -> dict[str, Any]:
    """Dados necessários para a emissão do certificado."""
    curso = inscricao.curso
    return {
        "user_id": inscricao.user_id,
        "course_id": curso.id,
        "enrollment_id": inscricao.id,
        "codigo": generate_public_code("CLOP-CERT-", 12),
    }
