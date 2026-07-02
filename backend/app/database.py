from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.config import get_settings  # noqa: E402 — after Base to break circular import

settings = get_settings()

_kw={} if settings.database_url.startswith("sqlite") else {"pool_size":settings.db_pool_size,"max_overflow":settings.db_max_overflow}
engine=create_engine(settings.database_url,pool_pre_ping=True,**_kw)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency: yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
