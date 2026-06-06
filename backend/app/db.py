"""SQLite database engine and session helpers."""
from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

# check_same_thread=False so FastAPI's threadpool workers can share the engine.
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create tables. Importing models registers them on SQLModel.metadata."""
    import app.models  # noqa: F401  (ensures models are registered)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    with Session(engine) as session:
        yield session
