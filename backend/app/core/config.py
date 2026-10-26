from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
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

    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/clop_academy"
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
