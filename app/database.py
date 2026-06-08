"""Подключение к SQLite через SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./planner.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно для SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Зависимость FastAPI: открывает сессию и гарантированно закрывает её."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
