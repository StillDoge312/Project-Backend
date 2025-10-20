import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_table_columns(table_name: str) -> set[str]:
    with engine.connect() as connection:
        result = connection.execute(text(f"PRAGMA table_info('{table_name}')"))
        return {row[1] for row in result.fetchall()}


def _ensure_column(table_name: str, column_sql: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))


def run_migrations() -> None:
    # Import models so that SQLAlchemy is aware of mapped tables before create_all
    from . import models  # noqa: F401  pylint: disable=unused-import,import-outside-toplevel

    ensure_database()

    Base.metadata.create_all(bind=engine)

    existing_tables = set()
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        existing_tables = {row[0] for row in rows.fetchall()}

    if "users" in existing_tables:
        columns = _get_table_columns("users")
        if "otp_secret" not in columns:
            _ensure_column("users", "otp_secret TEXT")
        if "is_2fa_enabled" not in columns:
            _ensure_column("users", "is_2fa_enabled BOOLEAN DEFAULT 0")
        if "last_login_at" not in columns:
            _ensure_column("users", "last_login_at DATETIME")

    if "credentials" not in existing_tables:
        Base.metadata.create_all(bind=engine)


__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "run_migrations",
]
