from __future__ import annotations

import re
import unicodedata
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")

_SLUG_STRIP = re.compile(r"[^\w\s-]", re.UNICODE)
_SLUG_HYPHENS = re.compile(r"[-\s]+")


def slugify(value: str) -> str:
    """Normaliza um texto para utilização em URLs legíveis."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_STRIP.sub("", ascii_text).strip().lower()
    slug = _SLUG_HYPHENS.sub("-", slug)
    return slug or "item"


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 12

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1, description="Número da página (começa em 1)."),
    page_size: int = Query(
        12, ge=1, le=100, description="Elementos por página (máximo 100)."
    ),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def build(cls, *, page: int, page_size: int, total: int) -> "PageMeta":
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(
            page=page, page_size=page_size, total=total, total_pages=total_pages
        )


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta
