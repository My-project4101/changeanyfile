# services/backend/app/db.py
from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_URL, BASE_DIR
from pathlib import Path

# If DATABASE_URL not set, fall back to SQLite dev database
if DATABASE_URL:
    db_url = DATABASE_URL
else:
    sqlite_path = Path(BASE_DIR) / "dev.sqlite"
    db_url = f"sqlite:///{sqlite_path}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, echo=False, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
