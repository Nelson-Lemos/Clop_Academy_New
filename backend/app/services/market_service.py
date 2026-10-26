from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.markets import PROVIDERS
from app.integrations.markets.base import ProviderResult
from app.models.market import (
    EconomicEvent,
    MacroIndicator,
    MarketInstrument,
    MarketQuote,
    MarketScope,
    QuoteFreshness,
)
from app.schemas.market import (
    EconomicEventOut,
    InstrumentOut,
    MacroIndicatorOut,
    MarketOverview,
    MarketSourceStatus,
    QuoteOut,
)

logger = logging.getLogger("clop.markets")

_cache: dict[str, tuple[float, object]] = {}


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value) -> None:
    _cache[key] = (time.time() + settings.MARKET_CACHE_TTL_SECONDS, value)


def clear_cache() -> None:
    _cache.clear()


def status_fontes() -> list[MarketSourceStatus]:
    statuses: list[MarketSourceStatus] = []
    for provider_class in PROVIDERS:
        provider = provider_class()
        info = provider.status()
        statuses.append(
            MarketSourceStatus(
                chave=info["chave"],
                nome=info["nome"],
                configurada=info["configurada"],
                estado=info["estado"],
                mensagem=info["mensagem"],
                url_base=info.get("url_base"),
            )
        )
    return statuses


def sincronizar_fontes(db: Session) -> list[ProviderResult]:
    """Consulta as fontes configuradas e grava os resultados na base de dados.

    Fontes não configuradas são ignoradas — os seus instrumentos mantêm o
    estado `NAO_DISPONIVEL` até existir uma fonte efectiva.
    """
    resultados: list[ProviderResult] = []

    for provider_class in PROVIDERS:
        provider = provider_class()
        if not provider.is_configured():
            continue

        result = provider.fetch_quotes()
        resultados.append(result)

        if not result.ok:
            logger.warning("Fonte %s indisponível: %s", provider.chave, result.mensagem)
            continue

        for quote in result.quotes:
            registo = (
                db.query(MarketQuote)
                .filter(
                    MarketQuote.simbolo == quote.simbolo,
                    MarketQuote.fonte == provider.nome,
                )
                .first()
            )
            if registo is None:
                registo = MarketQuote(
                    simbolo=quote.simbolo,
                    nome=quote.nome,
                    mercado=provider.mercado,
                    fonte=provider.nome,
                )
                db.add(registo)

            registo.nome = quote.nome
            registo.mercado = provider.mercado
            registo.preco = quote.preco
            registo.variacao = quote.variacao
            registo.variacao_percent = quote.variacao_percent
            registo.moeda = quote.moeda
            registo.unidade = quote.unidade
            registo.fonte_url = result.url_base
            registo.frescura = quote.frescura
            registo.data_mercado = quote.data_mercado
            registo.consultado_em = result.consultado_em
            registo.observacao = quote.observacao

    if resultados:
        db.commit()
        clear_cache()

    return resultados


def _cotacao_de(quote: MarketQuote | None) -> QuoteOut | None:
    if quote is None:
        return None
    return QuoteOut.model_validate(quote)


def overview(db: Session, *, mercado: str | None = None) -> MarketOverview:
    """Constrói o resumo do portal de mercados a partir dos dados disponíveis."""
    cached = _cache_get(f"overview:{mercado or 'TODOS'}")
    if cached is not None:
        return cached  # type: ignore[return-value]

    instrumentos = (
        db.query(MarketInstrument)
        .filter(MarketInstrument.ativa.is_(True))
        .order_by(MarketInstrument.mercado, MarketInstrument.nome)
        .all()
    )

    if mercado:
        instrumentos = [i for i in instrumentos if i.mercado == mercado]

    instrument_items: list[InstrumentOut] = []
    for instrument in instrumentos:
        quote = (
            db.query(MarketQuote)
            .filter(MarketQuote.simbolo == instrument.simbolo)
            .order_by(MarketQuote.consultado_em.desc())
            .first()
        )
        item = InstrumentOut.model_validate(instrument)
        item.cotacao = _cotacao_de(quote)
        instrument_items.append(item)

    indicadores = (
        db.query(MacroIndicator)
        .order_by(MacroIndicator.nome)
        .all()
    )
    indicator_items = [MacroIndicatorOut.model_validate(i) for i in indicadores]

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    calendario = (
        db.query(EconomicEvent)
        .filter(EconomicEvent.data >= agora - timedelta(days=1))
        .order_by(EconomicEvent.data)
        .limit(60)
        .all()
    )
    calendar_items = [EconomicEventOut.model_validate(e) for e in calendario]

    fontes = status_fontes()
    alguma_configurada = any(f.configurada for f in fontes)
    tem_dados = any(
        (i.cotacao and i.cotacao.preco is not None) for i in instrument_items
    ) or bool(indicator_items)

    if tem_dados:
        disponibilidade = "DISPONIVEL"
        aviso = (
            "Os dados apresentados são de caráter informativo e educativo e não "
            "constituem aconselhamento financeiro. Verifique sempre a fonte e a "
            "data de cada valor junto do emissor oficial."
        )
    elif alguma_configurada:
        disponibilidade = "SEM_DADOS"
        aviso = (
            "As fontes estão configuradas mas ainda não devolveram dados. "
            "Tente novamente dentro de alguns minutos."
        )
    else:
        disponibilidade = "NAO_CONFIGURADO"
        aviso = (
            "As integrações de dados de mercado ainda não estão configuradas. "
            "A CLOP Academy apresenta, para já, apenas a informação "
            "institucional sobre o mercado angolano e o calendário de eventos. "
            "Consulte a administração para activar as fontes oficiais."
        )

    result = MarketOverview(
        gerado_em=agora,
        disponibilidade=disponibilidade,
        aviso=aviso,
        fontes=fontes,
        instrumentos=instrument_items,
        indicadores=indicator_items,
        calendario=calendar_items,
    )
    _cache_set(f"overview:{mercado or 'TODOS'}", result)
    return result


def instrumentos_disponiveis(db: Session, mercado: str = MarketScope.INTERNACIONAL):
    return (
        db.query(MarketInstrument)
        .filter(
            MarketInstrument.mercado == mercado,
            MarketInstrument.ativa.is_(True),
        )
        .order_by(MarketInstrument.nome)
        .all()
    )
