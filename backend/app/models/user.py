from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole:
    """Perfis de utilizador da CLOP Academy."""

    STUDENT = "STUDENT"
    INSTRUCTOR = "INSTRUCTOR"
    EDITOR = "EDITOR"
    FINANCE = "FINANCE"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"


class UserStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(140), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.STUDENT, nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), default=UserStatus.ACTIVE, nullable=False, index=True
    )
    aceite_termos_em: Mapped[datetime | None] = mapped_column(DateTime)
    email_verificado_em: Mapped[datetime | None] = mapped_column(DateTime)
    ultimo_acesso_em: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    perfil_aluno: Mapped[StudentProfile | None] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    perfil_formador: Mapped[InstructorProfile | None] = relationship(
        "InstructorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    inscricoes: Mapped[list[Enrollment]] = relationship(  # noqa: F821
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
    certificates: Mapped[list[Certificate]] = relationship(  # noqa: F821
        "Certificate",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Certificate.user_id",
    )
    notificacoes: Mapped[list[Notification]] = relationship(  # noqa: F821
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    """Dados adicionais de um aluno."""

    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    profissao: Mapped[str | None] = mapped_column(String(120))
    empresa: Mapped[str | None] = mapped_column(String(140))
    cidade: Mapped[str | None] = mapped_column(String(80))
    provincia: Mapped[str | None] = mapped_column(String(80))
    nivel_educacao: Mapped[str | None] = mapped_column(String(80))
    area_interesse: Mapped[str | None] = mapped_column(String(160))
    objetivo: Mapped[str | None] = mapped_column(Text)
    biografia: Mapped[str | None] = mapped_column(Text)
    linkedin: Mapped[str | None] = mapped_column(String(255))
    newsletter_inscrito: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="perfil_aluno")


class InstructorProfile(Base):
    """Dados públicos de um formador."""

    __tablename__ = "instructor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    cargo: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    foto_url: Mapped[str | None] = mapped_column(String(255))
    site_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="perfil_formador")
