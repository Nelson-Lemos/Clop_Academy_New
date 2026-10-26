from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings
from app.integrations.markets.base import (
    MarketDataProvider,
    ProviderQuote,
    ProviderResult,
)
from app.models.market import QuoteFreshness

logger = logging.getLogger("clop.markets")


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return None


class HttpMarketProvider(MarketDataProvider):
    """Adaptador base para fontes de dados servidas por HTTP.

    Contrato de resposta esperado (JSON):

    ```json
    {
      "quotes": [
        {
          "symbol": "SPX",
          "name": "S&P 500",
          "price": 5000.12,
          "change": 12.3,
          "change_percent": 0.25,
          "currency": "USD",
          "market_time": "2026-01-02T18:00:00Z",
          "freshness": "TEMPO_REAL"
        }
      ]
    }
    ```
    """

    chave = "HTTP"
    nome = "Fonte HTTP"
    freshness_default = QuoteFreshness.TEMPO_REAL

    def __init__(self, *, api_url: str, api_key: str, chave: str, nome: str, mercado: str):
        self.api_url = (api_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.chave = chave
        self.nome = nome
        self.mercado = mercado

    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def fetch_quotes(self) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                ok=False,
                mensagem="Fonte não configurada.",
                url_base=self.api_url or None,
            )

        url = f"{self.api_url}/quotes"
        try:
            with httpx.Client(
                timeout=settings.MARKET_REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = client.get(url, headers=self._headers())
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Falha HTTP na fonte %s: %s", self.chave, exc)
            return ProviderResult(
                ok=False,
                mensagem=f"Falha na consulta à fonte ({exc.response.status_code}).",
                url_base=self.api_url,
            )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Falha na fonte %s: %s", self.chave, exc)
            return ProviderResult(
                ok=False, mensagem="Não foi possível obter dados da fonte.", url_base=self.api_url
            )

        raw_quotes = payload.get("quotes") if isinstance(payload, dict) else payload
        if not isinstance(raw_quotes, list):
            return ProviderResult(
                ok=False,
                mensagem="Resposta da fonte sem a lista de cotações esperada.",
                url_base=self.api_url,
            )

        quotes: list[ProviderQuote] = []
        for item in raw_quotes:
            if not isinstance(item, dict):
                continue
            simbolo = str(item.get("symbol") or item.get("simbolo") or "").strip()
            if not simbolo:
                continue
            quotes.append(
                ProviderQuote(
                    simbolo=simbolo,
                    nome=str(item.get("name") or item.get("nome") or simbolo),
                    preco=_to_decimal(item.get("price") if item.get("price") is not None else item.get("preco")),
                    variacao=_to_decimal(item.get("change") if item.get("change") is not None else item.get("variacao")),
                    variacao_percent=_to_decimal(
                        item.get("change_percent")
                        if item.get("change_percent") is not None
                        else item.get("variacao_percent")
                    ),
                    moeda=item.get("currency") or item.get("moeda"),
                    unidade=item.get("unit") or item.get("unidade"),
                    data_mercado=_parse_datetime(
                        item.get("market_time") or item.get("data_mercado")
                    ),
                    frescura=str(item.get("freshness") or self.freshness_default),
                    observacao=item.get("note") or item.get("observacao"),
                )
            )

        return ProviderResult(
            ok=True,
            mensagem=f"{len(quotes)} cotações obtidas.",
            quotes=quotes,
            url_base=self.api_url,
        )


class InternationalMarketsProvider(HttpMarketProvider):
    chave = "MERCADOS_INTERNACIONAIS"
    nome = "Mercados internacionais"
    mercado = "INTERNACIONAL"

    def __init__(self) -> None:
        super().__init__(
            api_url=settings.MARKET_INTERNATIONAL_API_URL,
            api_key=settings.MARKET_INTERNATIONAL_API_KEY,
            chave=self.chave,
            nome=self.nome,
            mercado=self.mercado,
        )


class BodivaProvider(HttpMarketProvider):
    chave = "BODIVA"
    nome = "Bolsa de Valores e Derivativos de Angola (BODIVA)"
    mercado = "ANGOLA"
    freshness_default = QuoteFreshness.ATRASADO

    def __init__(self) -> None:
        super().__init__(
            api_url=settings.MARKET_BODIVA_API_URL,
            api_key=settings.MARKET_BODIVA_API_KEY,
            chave=self.chave,
            nome=self.nome,
            mercado=self.mercado,
        )

    def fetch_quotes(self) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult(
                ok=False,
                mensagem=(
                    "Integração BODIVA não configurada. Registe-se em "
                    "https://www.bodiva.ao e solicite as credenciais de acesso "
                    "para activar a consulta."
                ),
                url_base=self.api_url or None,
            )
        return super().fetch_quotes()
