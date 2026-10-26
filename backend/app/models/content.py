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


class ArticleType:
    """Natureza do conteúdo editorial.

    Distingue informação factual de opinião e de material educativo.
    """

    NOTICIA = "NOTICIA"
    ANALISE = "ANALISE"
    OPINIAO = "OPINIAO"
    EDUCATIVO = "EDUCATIVO"


class ArticleStatus:
    RASCUNHO = "RASCUNHO"
    AGENDADO = "AGENDADO"
    PUBLICADO = "PUBLICADO"
    ARQUIVADO = "ARQUIVADO"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    cor: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    artigos: Mapped[list[Article]] = relationship(
        "Article", back_populates="categoria"
    )
    eventos: Mapped[list[Event]] = relationship("Event", back_populates="categoria")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(220), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True, nullable=False)
    resumo: Mapped[str] = mapped_column(String(500), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    tipo: Mapped[str] = mapped_column(
        String(20), default=ArticleType.NOTICIA, nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), default=ArticleStatus.RASCUNHO, nullable=False, index=True
    )
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    autor_nome: Mapped[str | None] = mapped_column(String(140))
    fonte: Mapped[str | None] = mapped_column(String(160))
    fonte_url: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[str | None] = mapped_column(String(400))
    publicado_em: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    agendado_para: Mapped[datetime | None] = mapped_column(DateTime)
    visualizacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped[Category | None] = relationship("Category", back_populates="artigos")
    autor: Mapped[User | None] = relationship("User")  # noqa: F821


class EventStatus:
    RASCUNHO = "RASCUNHO"
    PUBLICADO = "PUBLICADO"
    CANCELADO = "CANCELADO"
    CONCLUIDO = "CONCLUIDO"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    resumo: Mapped[str] = mapped_column(String(500), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    local: Mapped[str | None] = mapped_column(String(200))
    cidade: Mapped[str | None] = mapped_column(String(80))
    inicio: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    fim: Mapped[datetime | None] = mapped_column(DateTime)
    formato: Mapped[str] = mapped_column(String(30), default="PRESENCIAL", nullable=False)
    vagas: Mapped[int | None] = mapped_column(Integer)
    inscricoes_abertas: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    requer_inscricao: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    estado: Mapped[str] = mapped_column(
        String(20), default=EventStatus.RASCUNHO, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped[Category | None] = relationship("Category", back_populates="eventos")
    inscricoes: Mapped[list[EventRegistration]] = relationship(
        "EventRegistration", back_populates="evento", cascade="all, delete-orphan"
    )


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(30))
    notas: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="CONFIRMADA", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    evento: Mapped[Event] = relationship("Event", back_populates="inscricoes")


class CampaignStatus:
    PLANEADA = "PLANEADA"
    EM_CURSO = "EM_CURSO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class Campaign(Base):
    """Campanha institucional (divulgação de cursos, eventos, parcerias)."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    descricao: Mapped[str] = mapped_column(Text)
    objetivo: Mapped[str | None] = mapped_column(String(160))
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    link_destino: Mapped[str | None] = mapped_column(String(500))
    texto_botao: Mapped[str | None] = mapped_column(String(60))
    estado: Mapped[str] = mapped_column(
        String(20), default=CampaignStatus.PLANEADA, nullable=False, index=True
    )
    data_inicio: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    data_fim: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    destaque_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visualizacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cliques: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Advertisement(Base):
    """Espaço publicitário configurável."""

    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    link_destino: Mapped[str | None] = mapped_column(String(500))
    posicao: Mapped[str] = mapped_column(String(40), default="SIDEBAR", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    data_inicio: Mapped[datetime | None] = mapped_column(DateTime)
    data_fim: Mapped[datetime | None] = mapped_column(DateTime)
    impressoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cliques: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ProjectStatus:
    PLANEADO = "PLANEADO"
    EM_CURSO = "EM_CURSO"
    CONCLUIDO = "CONCLUIDO"


class Project(Base):
    """Projecto ou iniciativa institucional."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    resumo: Mapped[str] = mapped_column(String(500), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    area: Mapped[str | None] = mapped_column(String(80), index=True)
    estado: Mapped[str] = mapped_column(
        String(20), default=ProjectStatus.PLANEADO, nullable=False, index=True
    )
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    inicio: Mapped[datetime | None] = mapped_column(DateTime)
    conclusao_prevista: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
