from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class MessageOut(BaseModel):
    mensagem: str
    detalhe: str | None = None


class ContactMessageCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=140)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=30)
    assunto: str = Field(min_length=3, max_length=200)
    categoria: str = Field(default="GERAL", max_length=60)
    mensagem: str = Field(min_length=10, max_length=5000)


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    telefone: str | None = None
    assunto: str
    categoria: str
    mensagem: str
    estado: str
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )


class ContactMessageUpdate(BaseModel):
    estado: str


class NewsletterCreate(BaseModel):
    email: EmailStr
    nome: str | None = Field(default=None, max_length=140)
    consentimento: bool = False
    origem: str | None = Field(default=None, max_length=60)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    mensagem: str
    tipo: str
    ligacao: str | None = None
    lida: bool
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    utilizador_nome: str | None = None
    action: str
    entity: str | None = None
    entity_id: int | None = None
    detalhe: str | None = None
    ip_address: str | None = None
    created_at: datetime


class InstitutionOut(BaseModel):
    nome: str
    area: str
    assinatura: str
    slogan: str
    missao: str
    visao: str
    valores: list[str]
    areas_actuacao: list[dict]
    morada: str
    unitel: str
    africell: str
    email: str
    cidade: str
    pais: str
    redes_sociais: dict[str, str]


class DashboardMetrics(BaseModel):
    """Métricas obtidas da base de dados (nunca números inventados)."""

    alunos_registados: int
    inscricoes_por_curso: list[dict]
    cursos_activos: int
    cursos_publicados: int
    pagamentos_pendentes: int
    pagamentos_confirmados: int
    total_inscricoes: int
    inscricoes_activas: int
    artigos_publicados: int
    eventos_publicados: int
    eventos_proximos: int
    pedidos_contacto: int
    certificados_emitidos: int
    avaliacoes_pendentes: int
