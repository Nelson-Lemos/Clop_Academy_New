from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    descricao: str | None = None
    cor: str | None = None


class CategoryCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, max_length=120)
    descricao: str | None = None
    cor: str | None = Field(default=None, max_length=10)


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    slug: str
    resumo: str
    imagem_url: str | None = None
    tipo: str
    categoria_nome: str | None = None
    categoria_slug: str | None = None
    autor_nome: str | None = None
    publicado_em: datetime | None = None
    leitura_minutos: int = 4


class ArticleDetailOut(ArticleOut):
    conteudo: str
    fonte: str | None = None
    fonte_url: str | None = None
    tags: str | None = None
    estado: str
    visualizacoes: int = 0
    atualizado_em: datetime


class ArticleCreate(BaseModel):
    titulo: str = Field(min_length=5, max_length=220)
    slug: str | None = Field(default=None, max_length=240)
    resumo: str = Field(min_length=10, max_length=500)
    conteudo: str = Field(min_length=10)
    imagem_url: str | None = Field(default=None, max_length=500)
    tipo: str = "NOTICIA"
    estado: str = "RASCUNHO"
    categoria_id: int | None = None
    autor_id: int | None = None
    autor_nome: str | None = Field(default=None, max_length=140)
    fonte: str | None = Field(default=None, max_length=160)
    fonte_url: str | None = Field(default=None, max_length=500)
    tags: str | None = Field(default=None, max_length=400)
    publicado_em: datetime | None = None
    agendado_para: datetime | None = None


class ArticleUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=5, max_length=220)
    resumo: str | None = Field(default=None, min_length=10, max_length=500)
    conteudo: str | None = Field(default=None, min_length=10)
    imagem_url: str | None = Field(default=None, max_length=500)
    tipo: str | None = None
    estado: str | None = None
    categoria_id: int | None = None
    autor_nome: str | None = Field(default=None, max_length=140)
    fonte: str | None = Field(default=None, max_length=160)
    fonte_url: str | None = Field(default=None, max_length=500)
    tags: str | None = Field(default=None, max_length=400)
    publicado_em: datetime | None = None
    agendado_para: datetime | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    slug: str
    resumo: str
    imagem_url: str | None = None
    local: str | None = None
    cidade: str | None = None
    inicio: datetime
    fim: datetime | None = None
    formato: str
    vagas: int | None = None
    inscricoes_abertas: bool
    requer_inscricao: bool
    estado: str
    categoria_nome: str | None = None
    lugares_disponiveis: int | None = None


class EventDetailOut(EventOut):
    descricao: str


class EventCreate(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    resumo: str = Field(min_length=10, max_length=500)
    descricao: str = Field(min_length=10)
    imagem_url: str | None = Field(default=None, max_length=500)
    local: str | None = Field(default=None, max_length=200)
    cidade: str | None = Field(default=None, max_length=80)
    inicio: datetime
    fim: datetime | None = None
    formato: str = "PRESENCIAL"
    vagas: int | None = Field(default=None, ge=1)
    inscricoes_abertas: bool = True
    requer_inscricao: bool = True
    categoria_id: int | None = None
    estado: str = "RASCUNHO"


class EventUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=5, max_length=200)
    resumo: str | None = Field(default=None, min_length=10, max_length=500)
    descricao: str | None = Field(default=None, min_length=10)
    imagem_url: str | None = Field(default=None, max_length=500)
    local: str | None = Field(default=None, max_length=200)
    cidade: str | None = Field(default=None, max_length=80)
    inicio: datetime | None = None
    fim: datetime | None = None
    formato: str | None = None
    vagas: int | None = Field(default=None, ge=1)
    inscricoes_abertas: bool | None = None
    requer_inscricao: bool | None = None
    categoria_id: int | None = None
    estado: str | None = None


class EventRegistrationCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=140)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=30)
    notas: str | None = Field(default=None, max_length=1000)


class EventRegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    nome: str
    email: EmailStr
    telefone: str | None = None
    estado: str
    criado_em: datetime


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    descricao: str | None = None
    objetivo: str | None = None
    imagem_url: str | None = None
    link_destino: str | None = None
    texto_botao: str | None = None
    estado: str
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    destaque_home: bool


class CampaignAdminOut(CampaignOut):
    visualizacoes: int = 0
    cliques: int = 0
    criado_em: datetime


class CampaignCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=180)
    slug: str | None = Field(default=None, max_length=200)
    descricao: str | None = None
    objetivo: str | None = Field(default=None, max_length=160)
    imagem_url: str | None = Field(default=None, max_length=500)
    link_destino: str | None = Field(default=None, max_length=500)
    texto_botao: str | None = Field(default=None, max_length=60)
    estado: str = "PLANEADA"
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    destaque_home: bool = False


class CampaignUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=180)
    descricao: str | None = None
    objetivo: str | None = Field(default=None, max_length=160)
    imagem_url: str | None = Field(default=None, max_length=500)
    link_destino: str | None = Field(default=None, max_length=500)
    texto_botao: str | None = Field(default=None, max_length=60)
    estado: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    destaque_home: bool | None = None


class AdvertisementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    imagem_url: str | None = None
    link_destino: str | None = None
    posicao: str


class AdvertisementCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=180)
    imagem_url: str | None = Field(default=None, max_length=500)
    link_destino: str | None = Field(default=None, max_length=500)
    posicao: str = "SIDEBAR"
    ativo: bool = True
    data_inicio: datetime | None = None
    data_fim: datetime | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    resumo: str
    descricao: str
    area: str | None = None
    estado: str
    imagem_url: str | None = None
    inicio: datetime | None = None
    conclusao_prevista: datetime | None = None


class ProjectCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=180)
    slug: str | None = Field(default=None, max_length=200)
    resumo: str = Field(min_length=10, max_length=500)
    descricao: str = Field(min_length=10)
    area: str | None = Field(default=None, max_length=80)
    estado: str = "PLANEADO"
    imagem_url: str | None = Field(default=None, max_length=500)
    inicio: datetime | None = None
    conclusao_prevista: datetime | None = None


class ProjectUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=180)
    resumo: str | None = Field(default=None, min_length=10, max_length=500)
    descricao: str | None = Field(default=None, min_length=10)
    area: str | None = Field(default=None, max_length=80)
    estado: str | None = None
    imagem_url: str | None = Field(default=None, max_length=500)
    inicio: datetime | None = None
    conclusao_prevista: datetime | None = None
