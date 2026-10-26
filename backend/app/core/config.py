from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    # O backend lê primeiro o seu .env e, depois, o .env.local da raiz
    # gerado por `neon deploy` (que tem precedência).
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "CLOP Academy"
    PROJECT_DESCRIPTION: str = (
        "Plataforma digital da CLOP Academia Digital, LDA. "
        "Educação Financeira & Mercados — Conhecimento que transforma "
        "oportunidades em resultados."
    )
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Connection string da base de dados. Em produção (Render) defina a
    # variável de ambiente DATABASE_URL com a connection string da base de
    # dados gerida — nunca localhost, porque a base de dados não corre no
    # mesmo container da aplicação.
    DATABASE_URL: str
    # URL direto (sem pooler) usado pelo Alembic em migrações.
    DATABASE_URL_UNPOOLED: str | None = None
    SECRET_KEY: str = "troque_este_segredo_por_um_valor_aleatorio"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    PUBLIC_SITE_URL: str = "http://localhost:5173"

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10

    SEED_ADMIN_EMAIL: str = "admin@clop.academy"
    SEED_ADMIN_PASSWORD: str = "TroqueEstaPassword_2026!"
    SEED_ADMIN_NAME: str = "Administrador CLOP"

    INSTITUTION_NAME: str = "CLOP Academia Digital, LDA."
    INSTITUTION_AREA: str = "Educação Financeira & Mercados"
    INSTITUTION_ADDRESS: str = (
        "Kinaxixi, Rua da Missão, Edifício 93, Apartamento 8A, Luanda, Angola"
    )
    INSTITUTION_UNITEL: str = "994 365 4853"
    INSTITUTION_AFRICELL: str = "955 517 094"
    INSTITUTION_EMAIL: str = "infocloptrader@gmail.com"
    # Redes sociais: "Facebook=https://...,LinkedIn=https://..."
    # Redes não configuradas não são apresentadas na interface.
    INSTITUTION_SOCIAL_LINKS: str = ""

    MARKET_INTERNATIONAL_API_URL: str = ""
    MARKET_INTERNATIONAL_API_KEY: str = ""
    MARKET_BODIVA_API_URL: str = ""
    MARKET_BODIVA_API_KEY: str = ""
    MARKET_CACHE_TTL_SECONDS: int = 300
    MARKET_REQUEST_TIMEOUT_SECONDS: int = 10

    @staticmethod
    def _with_psycopg_driver(url: str) -> str:
        """Garante o driver psycopg 3 nos URLs PostgreSQL da Neon."""
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL pooled usado pela aplicação (PgBouncer em modo transacção)."""
        return self._with_psycopg_driver(self.DATABASE_URL)

    @property
    def migration_database_url(self) -> str:
        """URL direto usado pelo Alembic (sem PgBouncer)."""
        return self._with_psycopg_driver(
            self.DATABASE_URL_UNPOOLED or self.DATABASE_URL
        )

    @field_validator("DATABASE_URL")
    @classmethod
    def _database_url_nao_aponta_localhost_em_producao(
        cls, v: str, info
    ) -> str:
        ambiente = str((info.data or {}).get("ENVIRONMENT", "development")).lower()
        if ambiente in {"production", "prod"} and any(
            host in v for host in ("localhost", "127.0.0.1")
        ):
            raise ValueError(
                "DATABASE_URL não pode apontar para localhost em produção. "
                "Defina a variável de ambiente DATABASE_URL com a connection "
                "string da base de dados do Render."
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
