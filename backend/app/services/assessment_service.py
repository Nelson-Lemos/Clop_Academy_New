from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.catalog import Enrollment, EnrollmentStatus
from app.models.enrollment import Assessment, Submission, SubmissionStatus
from app.models.messaging import NotificationType
from app.services.notification_service import notify


def _parse_opcoes(opcoes: str | None) -> list[str]:
    if not opcoes:
        return []
    try:
        parsed = json.loads(opcoes)
        if isinstance(parsed, list):
            return [str(o) for o in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [linha for linha in (opcoes or "").splitlines() if linha.strip()]


def opcoes_para_texto(opcoes: str | None) -> list[str]:
    return _parse_opcoes(opcoes)


def nota_porcentagem(avaliacao: Assessment, respostas: dict[str, str]) -> int:
    """Calcula a nota de uma submissão (percentagem de pontos correctos)."""
    total_pontos = sum(p.pontos for p in avaliacao.perguntas) or 1
    pontos_ganhos = 0

    for pergunta in avaliacao.perguntas:
        resposta = (respostas.get(str(pergunta.id)) or "").strip()
        if not resposta or not pergunta.resposta_correta:
            continue
        if resposta.strip().lower() == pergunta.resposta_correta.strip().lower():
            pontos_ganhos += pergunta.pontos

    return int(round(pontos_ganhos / total_pontos * 100))


def submeter(
    db: Session, *, inscricao: Enrollment, assessment_id: int, respostas: dict[str, str]
) -> Submission:
    """Regista a submissão de uma avaliação. A validação é feita no servidor."""
    avaliacao = db.get(Assessment, assessment_id)
    if avaliacao is None:
        raise ValueError("Avaliação inexistente.")
    if avaliacao.course_id != inscricao.course_id:
        raise ValueError("Avaliação não pertence ao curso desta inscrição.")
    if not avaliacao.published:
        raise ValueError("Esta avaliação não está disponível.")

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    if avaliacao.disponivel_de and agora < avaliacao.disponivel_de:
        raise ValueError("Esta avaliação ainda não está disponível.")
    if avaliacao.disponivel_ate and agora > avaliacao.disponivel_ate:
        raise ValueError("O prazo desta avaliação já expirou.")

    tentativas = (
        db.query(Submission)
        .filter(
            Submission.enrollment_id == inscricao.id,
            Submission.assessment_id == assessment_id,
        )
        .count()
    )
    if tentativas >= avaliacao.tentativas_maximas:
        raise ValueError("Número máximo de tentativas esgotado.")

    # Perguntas objectivas são corrigidas automaticamente no servidor.
    tem_resposta_correta = any(p.resposta_correta for p in avaliacao.perguntas)
    nota = nota_porcentagem(avaliacao, respostas) if tem_resposta_correta else None
    estado = SubmissionStatus.CORRIGIDA if nota is not None else SubmissionStatus.EM_CORRECAO

    submissao = Submission(
        assessment_id=assessment_id,
        enrollment_id=inscricao.id,
        user_id=inscricao.user_id,
        tentativa=tentativas + 1,
        estado=estado,
        nota=nota,
        respostas=json.dumps(respostas, ensure_ascii=False),
        submetida_em=agora,
        corrigida_em=agora if nota is not None else None,
    )
    db.add(submissao)
    db.flush()

    if nota is not None:
        notify(
            db,
            user_id=inscricao.user_id,
            titulo="Avaliação corrigida",
            mensagem=f"Recebeste a nota de {nota}% em «{avaliacao.titulo}».",
            tipo=NotificationType.AVALIACAO,
            ligacao=f"/aluno/avaliacoes/{assessment_id}",
        )
    return submissao


def corrigir(
    db: Session, *, submissao: Submission, nota: int, feedback: str | None, admin_id: int
) -> Submission:
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    submissao.nota = max(0, min(nota, 100))
    submissao.feedback = feedback
    submissao.estado = SubmissionStatus.CORRIGIDA
    submissao.corrigida_em = agora
    submissao.corrigida_por = admin_id

    notify(
        db,
        user_id=submissao.user_id,
        titulo="Avaliação corrigida",
        mensagem=(
            f"A tua avaliação «{submissao.avaliacao.titulo}» foi corrigida: "
            f"{submissao.nota}%."
        ),
        tipo=NotificationType.AVALIACAO,
        ligacao=f"/aluno/avaliacoes/{submissao.assessment_id}",
    )
    return submissao


def inscricao_activa(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    inscricao = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )
    if inscricao is None:
        return None
    if inscricao.estado not in {
        EnrollmentStatus.ACTIVA,
        EnrollmentStatus.CONCLUIDA,
        EnrollmentStatus.AGUARDA_PAGAMENTO,
        EnrollmentStatus.PENDENTE,
    }:
        return None
    return inscricao
