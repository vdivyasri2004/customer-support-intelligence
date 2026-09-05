from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()
import os

if settings.DATABASE_URL.startswith("sqlite"):
    DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    engine_kwargs = {"connect_args": {"check_same_thread": False}}
else:
    DB_PATH = None
    engine_kwargs = {"pool_pre_ping": True}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
