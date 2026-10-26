from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
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


class CourseStatus:
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class CourseModality:
    PRESENCIAL = "PRESENCIAL"
    ONLINE = "ONLINE"
    HIBRIDO = "HIBRIDO"


class CourseLevel:
    INICIADO = "INICIADO"
    INTERMEDIO = "INTERMEDIO"
    AVANCADO = "AVANCADO"


class EnrollmentStatus:
    PENDENTE = "PENDENTE"
    AGUARDA_PAGAMENTO = "AGUARDA_PAGAMENTO"
    ACTIVA = "ACTIVA"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
    REJEITADA = "REJEITADA"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    descricao_resumida: Mapped[str] = mapped_column(String(400), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    objetivos: Mapped[str | None] = mapped_column(Text)
    conteudo_programatico: Mapped[str | None] = mapped_column(Text)
    requisitos: Mapped[str | None] = mapped_column(Text)
    modalidade: Mapped[str] = mapped_column(
        String(20), default=CourseModality.ONLINE, nullable=False
    )
    nivel: Mapped[str] = mapped_column(
        String(20), default=CourseLevel.INICIADO, nullable=False
    )
    duracao_horas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    numero_aulas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preco: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    moeda: Mapped[str] = mapped_column(String(5), default="AOA", nullable=False)
    instructor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    area: Mapped[str | None] = mapped_column(String(80), index=True)
    estado: Mapped[str] = mapped_column(
        String(20), default=CourseStatus.DRAFT, nullable=False, index=True
    )
    vagas_maximas: Mapped[int | None] = mapped_column(Integer)
    inscricoes_abertas: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    percentagem_conclusao_minima: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )
    aulas_obrigatorias_minimas: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    instructor: Mapped[User | None] = relationship("User")  # noqa: F821
    modulos: Mapped[list[CourseModule]] = relationship(
        "CourseModule",
        back_populates="curso",
        cascade="all, delete-orphan",
        order_by="CourseModule.ordem",
    )
    turmas: Mapped[list[Cohort]] = relationship(
        "Cohort", back_populates="curso", cascade="all, delete-orphan"
    )


class CourseModule(Base):
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    curso: Mapped[Course] = relationship("Course", back_populates="modulos")
    aulas: Mapped[list[Lesson]] = relationship(
        "Lesson",
        back_populates="modulo",
        cascade="all, delete-orphan",
        order_by="Lesson.ordem",
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    modulo_id: Mapped[int] = mapped_column(
        ForeignKey("course_modules.id", ondelete="CASCADE"), index=True, nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20), default="VIDEO", nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duracao_minutos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conteudo: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(String(500))
    link_live: Mapped[str | None] = mapped_column(String(500))
    data_live: Mapped[datetime | None] = mapped_column(DateTime)
    obrigatoria: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    modulo: Mapped[CourseModule] = relationship("CourseModule", back_populates="aulas")
    materiais: Mapped[list[LessonMaterial]] = relationship(
        "LessonMaterial", back_populates="aula", cascade="all, delete-orphan"
    )


class LessonMaterial(Base):
    __tablename__ = "lesson_materials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aula_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20), default="FICHEIRO", nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    aula: Mapped[Lesson] = relationship("Lesson", back_populates="materiais")


class Cohort(Base):
    """Turma (coorte) de um curso."""

    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    instructor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    vagas: Mapped[int | None] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), default="ATIVA", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    curso: Mapped[Course] = relationship("Course", back_populates="turmas")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cohort_id: Mapped[int | None] = mapped_column(ForeignKey("cohorts.id"), index=True)
    estado: Mapped[str] = mapped_column(
        String(20), default=EnrollmentStatus.PENDENTE, nullable=False, index=True
    )
    preco_pago: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    termos_aceites: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    percentagem_progresso: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    iniciado_em: Mapped[datetime | None] = mapped_column(DateTime)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="inscricoes")  # noqa: F821
    curso: Mapped[Course] = relationship("Course")
    turma: Mapped[Cohort | None] = relationship("Cohort")
    progresso: Mapped[list[ProgressRecord]] = relationship(
        "ProgressRecord", back_populates="inscricao", cascade="all, delete-orphan"
    )


class ProgressRecord(Base):
    """Registo de conclusão de uma aula por parte de um aluno."""

    __tablename__ = "progress_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concludida: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    percentagem_video: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    ultima_posicao_segundos: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    inscricao: Mapped[Enrollment] = relationship("Enrollment", back_populates="progresso")
