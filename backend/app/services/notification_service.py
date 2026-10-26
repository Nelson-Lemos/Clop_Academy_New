from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.messaging import Notification, NotificationType


def create_notification(
    db: Session,
    *,
    user_id: int,
    titulo: str,
    mensagem: str,
    tipo: str = NotificationType.SISTEMA,
    ligacao: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        ligacao=ligacao,
    )
    db.add(notification)
    return notification


def notify(
    db: Session,
    *,
    user_id: int,
    titulo: str,
    mensagem: str,
    tipo: str = NotificationType.SISTEMA,
    ligacao: str | None = None,
) -> Notification:
    return create_notification(
        db,
        user_id=user_id,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        ligacao=ligacao,
    )
