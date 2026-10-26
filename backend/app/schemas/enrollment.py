from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class EnrollmentCreate(BaseModel):
    course_id: int
    cohort_id: int | None = None
    aceite_termos: bool = False


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    cohort_id: int | None = None
    estado: str
    preco_pago: Decimal
    termos_aceites: bool
    percentagem_progresso: int
    iniciado_em: datetime | None = None
    concluido_em: datetime | None = None
    # O modelo usa created_at; a API expõe criado_em.
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )


class EnrollmentCourseOut(EnrollmentOut):
    curso_nome: str
    curso_slug: str
    curso_imagem: str | None = None
    curso_modalidade: str
    curso_duracao_horas: int
    total_aulas: int = 0
    aulas_concluidas: int = 0
    proxima_aula: str | None = None
    proxima_aula_id: int | None = None
    avaliacoes_pendentes: int = 0
    certificado_disponivel: bool = False


class EnrollmentStateUpdate(BaseModel):
    estado: str
    motivo: str | None = Field(default=None, max_length=500)


class ProgressUpdate(BaseModel):
    lesson_id: int
    concluida: bool = True
    percentagem_video: int = Field(default=100, ge=0, le=100)
    ultima_posicao_segundos: int = Field(default=0, ge=0)


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enunciado: str
    tipo: str
    opcoes: str | None = None
    pontos: int
    ordem: int


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    module_id: int | None = None
    lesson_id: int | None = None
    titulo: str
    descricao: str | None = None
    tipo: str
    nota_maxima: int
    nota_aprovacao: int
    tempo_limite_minutos: int | None = None
    tentativas_maximas: int
    disponivel_de: datetime | None = None
    disponivel_ate: datetime | None = None
    perguntas: list[QuestionOut] = []
    total_perguntas: int = 0
    tentativas_usadas: int = 0
    ultima_nota: int | None = None
    ultima_submissao: datetime | None = None
    corrigida: bool = False


class AssessmentCreate(BaseModel):
    course_id: int
    module_id: int | None = None
    lesson_id: int | None = None
    titulo: str = Field(min_length=2, max_length=180)
    descricao: str | None = None
    tipo: str = "EXERCICIO"
    nota_maxima: int = Field(default=100, ge=1, le=1000)
    nota_aprovacao: int = Field(default=50, ge=0, le=1000)
    tempo_limite_minutos: int | None = Field(default=None, ge=1, le=600)
    tentativas_maximas: int = Field(default=3, ge=1, le=20)
    disponivel_de: datetime | None = None
    disponivel_ate: datetime | None = None
    published: bool = True
    perguntas: list["QuestionCreate"] = []


class QuestionCreate(BaseModel):
    enunciado: str = Field(min_length=3)
    tipo: str = "OPCAO_MULTIPLA"
    opcoes: str | None = None
    resposta_correta: str | None = None
    pontos: int = Field(default=1, ge=1, le=100)
    ordem: int = Field(default=0, ge=0)


class QuestionUpdate(BaseModel):
    enunciado: str | None = Field(default=None, min_length=3)
    tipo: str | None = None
    opcoes: str | None = None
    resposta_correta: str | None = None
    pontos: int | None = Field(default=None, ge=1, le=100)
    ordem: int | None = Field(default=None, ge=0)


class SubmissionCreate(BaseModel):
    assessment_id: int
    respostas: dict[str, str] = Field(default_factory=dict)


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    tentativa: int
    estado: str
    nota: int | None = None
    feedback: str | None = None
    submetida_em: datetime
    corrigida_em: datetime | None = None


class SubmissionGrade(BaseModel):
    nota: int = Field(ge=0, le=1000)
    feedback: str | None = Field(default=None, max_length=4000)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enrollment_id: int
    curso_id: int = Field(
        validation_alias=AliasChoices("curso_id", "course_id")
    )
    referencia: str
    valor: Decimal
    moeda: str
    metodo: str
    estado: str
    provider: str | None = None
    provider_reference: str | None = None
    notas: str | None = None
    confirmado_em: datetime | None = None
    criado_em: datetime = Field(
        validation_alias=AliasChoices("criado_em", "created_at")
    )


class PaymentAdminOut(PaymentOut):
    aluno_nome: str | None = None
    aluno_email: str | None = None
    curso_nome: str | None = None
    comprovativos: int = 0


class PaymentCreate(BaseModel):
    enrollment_id: int
    metodo: str = "MANUAL"
    notas: str | None = Field(default=None, max_length=1000)


class PaymentConfirm(BaseModel):
    estado: str = "CONFIRMADO"
    notas: str | None = Field(default=None, max_length=1000)


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    curso_id: int = Field(
        validation_alias=AliasChoices("curso_id", "course_id")
    )
    enrollment_id: int
    estado: str
    nota_final: int | None = None
    emitido_em: datetime
    curso_nome: str | None = None
    aluno_nome: str | None = None


class CertificatePublicOut(BaseModel):
    """Dados públicos mínimos para verificação de certificado."""

    codigo: str
    valido: bool
    estado: str
    aluno_nome: str | None = None
    curso_nome: str | None = None
    emitido_em: datetime | None = None
    nota_final: int | None = None


AssessmentCreate.model_rebuild()
