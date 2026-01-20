from sqlmodel import SQLModel, Session, create_engine

# SQLite database for local development
DATABASE_URL = "sqlite:///./dev.sqlite"

# SQLite needs this flag for multithreading (FastAPI + background tasks)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def init_db():
    """
    Create database tables.
    Called once on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Get a new database session.
    Caller is responsible for closing it.
    """
    return Session(engine)
