from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_database_url = settings.sqlalchemy_database_url

# O pooler da Neon (PgBouncer) corre em modo transacção e não suporta
# prepared statements. O psycopg 3 prepara após 5 execuções por omissão.
_connect_args: dict[str, object] = {}
if _database_url.startswith("postgresql+psycopg"):
    _connect_args["prepare_threshold"] = None

engine = create_engine(
    _database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    isolation_level="READ COMMITTED",
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
