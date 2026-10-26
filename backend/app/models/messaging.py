from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationType:
    INSCRICAO = "INSCRICAO"
    PAGAMENTO = "PAGAMENTO"
    AULA = "AULA"
    AVALIACAO = "AVALIACAO"
    CERTIFICADO = "CERTIFICADO"
    EVENTO = "EVENTO"
    COMUNICADO = "COMUNICADO"
    SISTEMA = "SISTEMA"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(30), default=NotificationType.SISTEMA, nullable=False
    )
    ligacao: Mapped[str | None] = mapped_column(String(400))
    lida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="notificacoes")  # noqa: F821


class ContactMessageStatus:
    NOVO = "NOVO"
    EM_ANALISE = "EM_ANALISE"
    RESPONDIDO = "RESPONDIDO"
    ARQUIVADO = "ARQUIVADO"


class ContactMessage(Base):
    """Pedido de contacto recebido através do formulário institucional."""

    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    assunto: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), default="GERAL", nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), default=ContactMessageStatus.NOVO, nullable=False, index=True
    )
    respondido_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    respondido_em: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    respondente: Mapped[User | None] = relationship("User")  # noqa: F821


class NewsletterSubscription(Base):
    __tablename__ = "newsletter_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nome: Mapped[str | None] = mapped_column(String(140))
    consentimento: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmacao_token: Mapped[str | None] = mapped_column(String(64), index=True)
    confirmado: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime)
    origem: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AuditAction:
    LOGIN = "LOGIN"
    LOGIN_FALHADO = "LOGIN_FALHADO"
    REGISTO = "REGISTO"
    ATUALIZAR_PERFIL = "ATUALIZAR_PERFIL"
    CRIAR_CURSO = "CRIAR_CURSO"
    ATUALIZAR_CURSO = "ATUALIZAR_CURSO"
    PUBLICAR_CURSO = "PUBLICAR_CURSO"
    CRIAR_INSCRICAO = "CRIAR_INSCRICAO"
    CANCELAR_INSCRICAO = "CANCELAR_INSCRICAO"
    ATUALIZAR_ESTADO_INSCRICAO = "ATUALIZAR_ESTADO_INSCRICAO"
    CRIAR_PAGAMENTO = "CRIAR_PAGAMENTO"
    CONFIRMAR_PAGAMENTO = "CONFIRMAR_PAGAMENTO"
    RECUSAR_PAGAMENTO = "RECUSAR_PAGAMENTO"
    SUBMETER_AVALIACAO = "SUBMETER_AVALIACAO"
    CORRIGIR_AVALIACAO = "CORRIGIR_AVALIACAO"
    EMITIR_CERTIFICADO = "EMITIR_CERTIFICADO"
    REVOGAR_CERTIFICADO = "REVOGAR_CERTIFICADO"
    CRIAR_ARTIGO = "CRIAR_ARTIGO"
    ATUALIZAR_ARTIGO = "ATUALIZAR_ARTIGO"
    PUBLICAR_ARTIGO = "PUBLICAR_ARTIGO"
    CRIAR_EVENTO = "CRIAR_EVENTO"
    ATUALIZAR_EVENTO = "ATUALIZAR_EVENTO"
    ATUALIZAR_CAMPANHA = "ATUALIZAR_CAMPANHA"
    ATUALIZAR_UTILIZADOR = "ATUALIZAR_UTILIZADOR"
    ATUALIZAR_PERMISSOES = "ATUALIZAR_PERMISSOES"
    ATUALIZAR_DADOS_MERCADO = "ATUALIZAR_DADOS_MERCADO"
    CONTACTO_RECEBIDO = "CONTACTO_RECEBIDO"
    NEWSLETTER = "NEWSLETTER"


class AuditLog(Base):
    """Registo de auditoria das operações sensíveis."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity: Mapped[str | None] = mapped_column(String(50), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    detalhe: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
