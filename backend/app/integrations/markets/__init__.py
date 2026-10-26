from __future__ import annotations

from app.integrations.markets.base import (
    MarketDataProvider,
    ProviderQuote,
    ProviderResult,
)
from app.integrations.markets.providers import BodivaProvider, InternationalMarketsProvider

__all__ = [
    "BodivaProvider",
    "InternationalMarketsProvider",
    "MarketDataProvider",
    "ProviderQuote",
    "ProviderResult",
    "PROVIDERS",
]

PROVIDERS: tuple[type[MarketDataProvider], ...] = (
    InternationalMarketsProvider,
    BodivaProvider,
)
