from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.messaging import AuditLog


def log_audit(
    db: Session,
    *,
    action: str,
    user_id: int | None = None,
    entity: str | None = None,
    entity_id: int | None = None,
    detalhe: str | None = None,
    request=None,
) -> AuditLog:
    """Regista uma operação sensível no registo de auditoria.

    Nunca são registadas palavras-passe, tokens ou comprovativos de pagamento.
    """
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detalhe=detalhe[:2000] if detalhe else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    return entry
