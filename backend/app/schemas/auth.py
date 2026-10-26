from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class RegisterRequest(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=140)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    aceite_termos: bool = False
    aceite_privacidade: bool = False
    profissao: str | None = Field(default=None, max_length=120)
    cidade: str | None = Field(default=None, max_length=80)
    provincia: str | None = Field(default=None, max_length=80)
    nivel_educacao: str | None = Field(default=None, max_length=80)
    objetivo: str | None = Field(default=None, max_length=2000)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profissao: str | None = None
    empresa: str | None = None
    cidade: str | None = None
    provincia: str | None = None
    nivel_educacao: str | None = None
    area_interesse: str | None = None
    objetivo: str | None = None
    biografia: str | None = None
    linkedin: str | None = None
    newsletter_inscrito: bool = False


class StudentProfileUpdate(BaseModel):
    nome_completo: str | None = Field(default=None, min_length=3, max_length=140)
    telefone: str | None = Field(default=None, max_length=30)
    profissao: str | None = Field(default=None, max_length=120)
    empresa: str | None = Field(default=None, max_length=140)
    cidade: str | None = Field(default=None, max_length=80)
    provincia: str | None = Field(default=None, max_length=80)
    nivel_educacao: str | None = Field(default=None, max_length=80)
    area_interesse: str | None = Field(default=None, max_length=160)
    objetivo: str | None = Field(default=None, max_length=2000)
    biografia: str | None = Field(default=None, max_length=2000)
    linkedin: str | None = Field(default=None, max_length=255)
    newsletter_inscrito: bool | None = None


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    email: EmailStr
    telefone: str | None = None
    role: str = UserRole.STUDENT
    estado: str = UserStatus.ACTIVE
    aceite_termos_em: datetime | None = None
    email_verificado_em: datetime | None = None
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )
    perfil_aluno: StudentProfileOut | None = None
    permissoes: list[str] = []


class AuthResponse(TokenResponse):
    user: MeOut


class PasswordChangeRequest(BaseModel):
    password_actual: str = Field(min_length=1, max_length=128)
    nova_password: str = Field(min_length=8, max_length=128)
