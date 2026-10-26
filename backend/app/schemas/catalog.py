from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class LessonMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None = None
    tipo: str
    url: str | None = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None = None
    tipo: str
    ordem: int
    duracao_minutos: int
    conteudo: str | None = None
    video_url: str | None = None
    link_live: str | None = None
    data_live: datetime | None = None
    obrigatoria: bool
    materiais: list[LessonMaterialOut] = []
    concluida: bool = False
    percentagem_video: int = 0
    ultima_posicao_segundos: int = 0


class CourseModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str | None = None
    ordem: int
    aulas: list[LessonOut] = []


class CohortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    data_inicio: date | None = None
    data_fim: date | None = None
    vagas: int | None = None
    estado: str


class InstructorOut(BaseModel):
    id: int
    nome_completo: str
    cargo: str | None = None
    bio: str | None = None
    foto_url: str | None = None


class CourseOut(BaseModel):
    """Projecção pública de um curso (usada em listagens)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    descricao_resumida: str
    descricao: str
    objetivos: str | None = None
    conteudo_programatico: str | None = None
    requisitos: str | None = None
    modalidade: str
    nivel: str
    duracao_horas: int
    numero_aulas: int
    preco: Decimal
    moeda: str
    imagem_url: str | None = None
    area: str | None = None
    estado: str
    inscricoes_abertas: bool
    vagas_maximas: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    formador: InstructorOut | None = None
    inscricoes_count: int = 0
    vagas_disponiveis: int | None = None


class CourseDetailOut(CourseOut):
    modulos: list[CourseModuleOut] = []
    turmas: list[CohortOut] = []
    percentagem_conclusao_minima: int = 100
    aulas_obrigatorias_minimas: int = 0


class CourseAdminOut(CourseDetailOut):
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )
    actualizado_em: datetime = Field(
        validation_alias=AliasChoices("actualizado_em", "updated_at")
    )


class CourseCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=180)
    slug: str | None = Field(default=None, max_length=200)
    descricao_resumida: str = Field(min_length=10, max_length=400)
    descricao: str = Field(min_length=10)
    objetivos: str | None = None
    conteudo_programatico: str | None = None
    requisitos: str | None = None
    modalidade: str = "ONLINE"
    nivel: str = "INICIADO"
    duracao_horas: int = Field(default=0, ge=0, le=10000)
    numero_aulas: int = Field(default=0, ge=0, le=1000)
    preco: Decimal = Field(default=Decimal("0.00"), ge=0)
    moeda: str = Field(default="AOA", max_length=5)
    instructor_id: int | None = None
    imagem_url: str | None = Field(default=None, max_length=500)
    area: str | None = Field(default=None, max_length=80)
    estado: str = "DRAFT"
    vagas_maximas: int | None = Field(default=None, ge=1)
    inscricoes_abertas: bool = True
    data_inicio: date | None = None
    data_fim: date | None = None
    percentagem_conclusao_minima: int = Field(default=100, ge=1, le=100)
    aulas_obrigatorias_minimas: int = Field(default=0, ge=0)


class CourseUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=180)
    descricao_resumida: str | None = Field(default=None, min_length=10, max_length=400)
    descricao: str | None = Field(default=None, min_length=10)
    objetivos: str | None = None
    conteudo_programatico: str | None = None
    requisitos: str | None = None
    modalidade: str | None = None
    nivel: str | None = None
    duracao_horas: int | None = Field(default=None, ge=0, le=10000)
    numero_aulas: int | None = Field(default=None, ge=0, le=1000)
    preco: Decimal | None = Field(default=None, ge=0)
    instructor_id: int | None = None
    imagem_url: str | None = Field(default=None, max_length=500)
    area: str | None = Field(default=None, max_length=80)
    estado: str | None = None
    vagas_maximas: int | None = Field(default=None, ge=1)
    inscricoes_abertas: bool | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    percentagem_conclusao_minima: int | None = Field(default=None, ge=1, le=100)
    aulas_obrigatorias_minimas: int | None = Field(default=None, ge=0)


class ModuleCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=180)
    descricao: str | None = None
    ordem: int = Field(default=0, ge=0)
    aulas: list["LessonCreate"] = []


class LessonCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=180)
    descricao: str | None = None
    tipo: str = "VIDEO"
    ordem: int = Field(default=0, ge=0)
    duracao_minutos: int = Field(default=0, ge=0, le=10000)
    conteudo: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    link_live: str | None = Field(default=None, max_length=500)
    data_live: datetime | None = None
    obrigatoria: bool = True


class LessonUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=2, max_length=180)
    descricao: str | None = None
    tipo: str | None = None
    ordem: int | None = Field(default=None, ge=0)
    duracao_minutos: int | None = Field(default=None, ge=0, le=10000)
    conteudo: str | None = None
    video_url: str | None = Field(default=None, max_length=500)
    link_live: str | None = Field(default=None, max_length=500)
    data_live: datetime | None = None
    obrigatoria: bool | None = None


class MaterialCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=180)
    descricao: str | None = None
    tipo: str = "FICHEIRO"
    url: str | None = Field(default=None, max_length=500)


class CohortCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    instructor_id: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    vagas: int | None = Field(default=None, ge=1)
    estado: str = "ATIVA"


ModuleCreate.model_rebuild()
