from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    simbolo: str
    nome: str
    mercado: str
    tipo: str
    preco: Decimal | None = None
    variacao: Decimal | None = None
    variacao_percent: Decimal | None = None
    moeda: str | None = None
    unidade: str | None = None
    fonte: str
    fonte_url: str | None = None
    frescura: str
    data_mercado: datetime | None = None
    consultado_em: datetime
    observacao: str | None = None


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    simbolo: str
    nome: str
    mercado: str
    tipo: str
    descricao: str | None = None
    emissor: str | None = None
    moeda: str | None = None
    cotacao: QuoteOut | None = None


class MacroIndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    pais: str
    valor: str | None = None
    unidade: str | None = None
    periodo: str | None = None
    variacao: str | None = None
    fonte: str
    fonte_url: str | None = None
    data_referencia: datetime | None = None
    consultado_em: datetime
    estado: str


class EconomicEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: datetime
    pais: str
    evento: str
    periodo: str | None = None
    previsao: str | None = None
    anterior: str | None = None
    impacto: str
    fonte: str | None = None


class MarketSourceStatus(BaseModel):
    """Estado de cada fonte de dados integrada."""

    chave: str
    nome: str
    configurada: bool
    estado: str
    mensagem: str | None = None
    url_base: str | None = None


class MarketOverview(BaseModel):
    gerado_em: datetime
    disponibilidade: str
    aviso: str
    fontes: list[MarketSourceStatus] = []
    instrumentos: list[InstrumentOut] = []
    indicadores: list[MacroIndicatorOut] = []
    calendario: list[EconomicEventOut] = []


class QuoteCreate(BaseModel):
    simbolo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=1, max_length=160)
    mercado: str = "INTERNACIONAL"
    tipo: str = "INDICE"
    preco: Decimal | None = None
    variacao: Decimal | None = None
    variacao_percent: Decimal | None = None
    moeda: str | None = Field(default=None, max_length=8)
    unidade: str | None = Field(default=None, max_length=40)
    fonte: str = Field(min_length=2, max_length=120)
    fonte_url: str | None = Field(default=None, max_length=500)
    frescura: str = "HISTORICO"
    data_mercado: datetime | None = None
    observacao: str | None = None
    instrument_id: int | None = None


class IndicatorCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=1, max_length=160)
    pais: str = Field(min_length=1, max_length=80)
    valor: str | None = Field(default=None, max_length=80)
    unidade: str | None = Field(default=None, max_length=40)
    periodo: str | None = Field(default=None, max_length=40)
    variacao: str | None = Field(default=None, max_length=40)
    fonte: str = Field(min_length=2, max_length=160)
    fonte_url: str | None = Field(default=None, max_length=500)
    data_referencia: datetime | None = None
    estado: str = "HISTORICO"


class EconomicEventCreate(BaseModel):
    data: datetime
    pais: str = Field(min_length=1, max_length=80)
    evento: str = Field(min_length=2, max_length=200)
    periodo: str | None = Field(default=None, max_length=40)
    previsao: str | None = Field(default=None, max_length=80)
    anterior: str | None = Field(default=None, max_length=80)
    impacto: str = "MEDIO"
    fonte: str | None = Field(default=None, max_length=160)
