from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CertificateStatus:
    EMITIDO = "EMITIDO"
    REVOGADO = "REVOGADO"


class Certificate(Base):
    """Certificado de conclusão emitido após verificação de requisitos."""

    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_certificate_user_course"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    codigo: Mapped[str] = mapped_column(
        String(40), unique=True, index=True, nullable=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), default=CertificateStatus.EMITIDO, nullable=False
    )
    nota_final: Mapped[int | None] = mapped_column(Integer)
    emitido_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    emitido_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime)
    motivo_revogacao: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User | None] = relationship(  # noqa: F821
        "User", back_populates="certificates", foreign_keys="Certificate.user_id"
    )
    admin_emissor: Mapped[User | None] = relationship(  # noqa: F821
        "User", foreign_keys="Certificate.emitido_por"
    )
    curso: Mapped[Course] = relationship("Course")  # noqa: F821


class MarketScope:
    INTERNACIONAL = "INTERNACIONAL"
    ANGOLA = "ANGOLA"


class MarketInstrumentType:
    INDICE = "INDICE"
    FOREX = "FOREX"
    MATERIA_PRIMA = "MATERIA_PRIMA"
    OBRIGACAO = "OBRIGACAO"
    ACAO = "ACAO"
    INDICADOR = "INDICADOR"


class QuoteFreshness:
    """Estado de actualização do dado de mercado."""

    TEMPO_REAL = "TEMPO_REAL"
    ATRASADO = "ATRASADO"
    HISTORICO = "HISTORICO"
    NAO_DISPONIVEL = "NAO_DISPONIVEL"


class MarketQuote(Base):
    """Cotação/instrumento de mercado com metadados de proveniência.

    `fonte` indica a origem do valor; `data_mercado` o momento a que o dado
    respeita; `consultado_em` o momento em que foi obtido; `frescura` o grau de
    actualização. Sem fonte configurada o registo é criado em estado
    `NAO_DISPONIVEL` — nunca são apresentados valores fictícios.
    """

    __tablename__ = "market_quotes"
    __table_args__ = (
        UniqueConstraint("simbolo", "fonte", name="uq_market_quote_symbol_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    simbolo: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    mercado: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(30), default=MarketInstrumentType.INDICE, nullable=False
    )
    preco: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    variacao: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    variacao_percent: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    moeda: Mapped[str | None] = mapped_column(String(8))
    unidade: Mapped[str | None] = mapped_column(String(40))
    fonte: Mapped[str] = mapped_column(String(120), nullable=False)
    fonte_url: Mapped[str | None] = mapped_column(String(500))
    frescura: Mapped[str] = mapped_column(
        String(20), default=QuoteFreshness.NAO_DISPONIVEL, nullable=False, index=True
    )
    data_mercado: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    consultado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    instruments: Mapped[list[MarketInstrument]] = relationship(
        "MarketInstrument", back_populates="quote", cascade="all, delete-orphan"
    )


class MarketInstrument(Base):
    """Descrição estática de um instrumento negociável."""

    __tablename__ = "market_instruments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    simbolo: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    mercado: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    emissor: Mapped[str | None] = mapped_column(String(160))
    moeda: Mapped[str | None] = mapped_column(String(8))
    quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_quotes.id", ondelete="SET NULL"), index=True
    )
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    quote: Mapped[MarketQuote | None] = relationship(
        "MarketQuote", back_populates="instruments"
    )


class EconomicEvent(Base):
    """Calendário económico."""

    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(80), nullable=False)
    evento: Mapped[str] = mapped_column(String(200), nullable=False)
    periodo: Mapped[str | None] = mapped_column(String(40))
    previsao: Mapped[str | None] = mapped_column(String(80))
    anterior: Mapped[str | None] = mapped_column(String(80))
    impacto: Mapped[str] = mapped_column(String(20), default="MEDIO", nullable=False)
    fonte: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MacroIndicator(Base):
    """Indicador macro-económico com origem e data."""

    __tablename__ = "macro_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    pais: Mapped[str] = mapped_column(String(80), nullable=False)
    valor: Mapped[str | None] = mapped_column(String(80))
    unidade: Mapped[str | None] = mapped_column(String(40))
    periodo: Mapped[str | None] = mapped_column(String(40))
    variacao: Mapped[str | None] = mapped_column(String(40))
    fonte: Mapped[str] = mapped_column(String(160), nullable=False)
    fonte_url: Mapped[str | None] = mapped_column(String(500))
    data_referencia: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    consultado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), default=QuoteFreshness.NAO_DISPONIVEL, nullable=False
    )
