"""Arquitectura de integração de dados de mercados.

Os adaptadores de dados estão completamente separados do código de
apresentação. Cada adaptador implementa `MarketDataProvider` e sabe:

* se está configurado (`is_configured`);
* como obter os dados (`fetch_quotes`);
* qual a fonte, a data do dado e o grau de actualização.

Se uma fonte não estiver configurada, o adaptador devolve um estado
informativo — nunca são apresentados valores fictícios como cotações reais.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class ProviderQuote:
    simbolo: str
    nome: str
    preco: Decimal | None = None
    variacao: Decimal | None = None
    variacao_percent: Decimal | None = None
    moeda: str | None = None
    unidade: str | None = None
    data_mercado: datetime | None = None
    frescura: str = "NAO_DISPONIVEL"
    observacao: str | None = None


@dataclass
class ProviderResult:
    ok: bool
    mensagem: str
    quotes: list[ProviderQuote] = field(default_factory=list)
    consultado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    url_base: str | None = None


class MarketDataProvider(ABC):
    chave: str = "PROVEDOR"
    nome: str = "Provedor"
    mercado: str = "INTERNACIONAL"

    @abstractmethod
    def is_configured(self) -> bool:
        """Indica se a fonte dispõe de credenciais/endpoint configurados."""

    @abstractmethod
    def fetch_quotes(self) -> ProviderResult:
        """Obtém as cotações junto da fonte configurada."""

    def status(self) -> dict:
        return {
            "chave": self.chave,
            "nome": self.nome,
            "mercado": self.mercado,
            "configurada": self.is_configured(),
            "estado": "CONFIGURADA" if self.is_configured() else "NAO_CONFIGURADA",
            "mensagem": (
                None
                if self.is_configured()
                else "Fonte não configurada. Defina as variáveis de ambiente "
                "correspondentes para activar a consulta."
            ),
            "url_base": None,
        }
