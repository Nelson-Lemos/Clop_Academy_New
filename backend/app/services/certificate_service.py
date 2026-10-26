from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.market import Certificate, CertificateStatus
from app.models.messaging import NotificationType
from app.services.enrollment_service import dados_certificado, requisitos_certificado
from app.services.notification_service import notify


def emitir_certificado(db: Session, inscricao_id: int, emitido_por: int | None = None):
    """Emite um certificado apenas após verificação dos requisitos do curso."""
    from app.models.catalog import Enrollment

    inscricao = db.get(Enrollment, inscricao_id)
    if inscricao is None:
        raise ValueError("Inscrição inexistente.")

    conforme, motivo = requisitos_certificado(inscricao)
    if not conforme:
        raise ValueError(motivo or "Requisitos de conclusão não cumpridos.")

    existente = (
        db.query(Certificate)
        .filter(
            Certificate.user_id == inscricao.user_id,
            Certificate.course_id == inscricao.course_id,
        )
        .first()
    )
    if existente is not None:
        if existente.estado == CertificateStatus.REVOGADO:
            existente.estado = CertificateStatus.EMITIDO
            existente.revogado_em = None
            existente.motivo_revogacao = None
            existente.emitido_em = datetime.now(timezone.utc).replace(tzinfo=None)
            db.flush()
            return existente
        return existente

    dados = dados_certificado(inscricao)
    certificado = Certificate(
        **dados,
        emitido_por=emitido_por,
        emitido_em=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(certificado)
    db.flush()

    notify(
        db,
        user_id=inscricao.user_id,
        titulo="Certificado emitido",
        mensagem=(
            f"O certificado de «{inscricao.curso.nome}» foi emitido. "
            "Podes consultá-lo e partilhá-lo na tua área do aluno."
        ),
        tipo=NotificationType.CERTIFICADO,
        ligacao=f"/aluno/certificados",
    )
    return certificado


def revogar_certificado(db: Session, certificado_id: int, motivo: str) -> Certificate:
    certificado = db.get(Certificate, certificado_id)
    if certificado is None:
        raise ValueError("Certificado inexistente.")
    certificado.estado = CertificateStatus.REVOGADO
    certificado.revogado_em = datetime.now(timezone.utc).replace(tzinfo=None)
    certificado.motivo_revogacao = motivo
    db.flush()
    return certificado


def verificar_certificado(db: Session, codigo: str):
    """Verificação pública: devolve apenas os dados estritamente necessários."""
    certificado = (
        db.query(Certificate).filter(Certificate.codigo == codigo.strip().upper()).first()
    )
    if certificado is None:
        return None
    return certificado
