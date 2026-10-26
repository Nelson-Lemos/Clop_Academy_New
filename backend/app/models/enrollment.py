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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentStatus:
    PENDENTE = "PENDENTE"
    EM_PROCESSAMENTO = "EM_PROCESSAMENTO"
    CONFIRMADO = "CONFIRMADO"
    RECUSADO = "RECUSADO"
    REEMBOLSADO = "REEMBOLSADO"
    CANCELADO = "CANCELADO"


class PaymentMethod:
    MANUAL = "MANUAL"
    TRANSFERENCIA = "TRANSFERENCIA"
    MPESA = "MPESA"
    UNITEL_MONEY = "UNITEL_MONEY"
    CARTAO = "CARTAO"
    STRIPE = "STRIPE"


class AssessmentType:
    EXERCICIO = "EXERCICIO"
    TESTE = "TESTE"
    TRABALHO = "TRABALHO"


class SubmissionStatus:
    EM_CORRECAO = "EM_CORRECAO"
    CORRIGIDA = "CORRIGIDA"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    referencia: Mapped[str] = mapped_column(
        String(40), unique=True, index=True, nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moeda: Mapped[str] = mapped_column(String(5), default="AOA", nullable=False)
    metodo: Mapped[str] = mapped_column(
        String(30), default=PaymentMethod.MANUAL, nullable=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), default=PaymentStatus.PENDENTE, nullable=False, index=True
    )
    provider: Mapped[str | None] = mapped_column(String(40))
    provider_reference: Mapped[str | None] = mapped_column(String(120), index=True)
    notas: Mapped[str | None] = mapped_column(Text)
    confirmado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    enrollment: Mapped[Enrollment] = relationship("Enrollment")  # noqa: F821
    user: Mapped[User | None] = relationship(  # noqa: F821
        "User", foreign_keys="Payment.user_id"
    )
    admin_confirmador: Mapped[User | None] = relationship(  # noqa: F821
        "User", foreign_keys="Payment.confirmado_por"
    )
    curso: Mapped[Course] = relationship("Course")  # noqa: F821
    comprovativos: Mapped[list[PaymentReceipt]] = relationship(
        "PaymentReceipt", back_populates="pagamento", cascade="all, delete-orphan"
    )


class PaymentReceipt(Base):
    """Comprovativo enviado pelo aluno para validação manual."""

    __tablename__ = "payment_receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nome_ficheiro: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer)
    enviado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pagamento: Mapped[Payment] = relationship("Payment", back_populates="comprovativos")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    module_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_modules.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[int | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(
        String(20), default=AssessmentType.EXERCICIO, nullable=False
    )
    nota_maxima: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    nota_aprovacao: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    tempo_limite_minutos: Mapped[int | None] = mapped_column(Integer)
    tentativas_maximas: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    disponivel_de: Mapped[datetime | None] = mapped_column(DateTime)
    disponivel_ate: Mapped[datetime | None] = mapped_column(DateTime)
    published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    curso: Mapped[Course] = relationship("Course")  # noqa: F821
    modulo: Mapped[CourseModule] = relationship("CourseModule")  # noqa: F821
    aula: Mapped[Lesson] = relationship("Lesson")  # noqa: F821
    perguntas: Mapped[list[Question]] = relationship(
        "Question", back_populates="avaliacao", cascade="all, delete-orphan"
    )
    submissoes: Mapped[list[Submission]] = relationship(
        "Submission", back_populates="avaliacao", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(20), default="OPCAO_MULTIPLA", nullable=False
    )
    opcoes: Mapped[str | None] = mapped_column(Text)
    resposta_correta: Mapped[str | None] = mapped_column(Text)
    pontos: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    avaliacao: Mapped[Assessment] = relationship("Assessment", back_populates="perguntas")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tentativa: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), default=SubmissionStatus.EM_CORRECAO, nullable=False
    )
    nota: Mapped[int | None] = mapped_column(Integer)
    feedback: Mapped[str | None] = mapped_column(Text)
    respostas: Mapped[str | None] = mapped_column(Text)
    submetida_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    corrigida_em: Mapped[datetime | None] = mapped_column(DateTime)
    corrigida_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    avaliacao: Mapped[Assessment] = relationship("Assessment", back_populates="submissoes")
    enrollment: Mapped[Enrollment] = relationship("Enrollment")  # noqa: F821
    user: Mapped[User | None] = relationship(  # noqa: F821
        "User", foreign_keys="Submission.user_id"
    )
    admin_corrector: Mapped[User | None] = relationship(  # noqa: F821
        "User", foreign_keys="Submission.corrigida_por"
    )
