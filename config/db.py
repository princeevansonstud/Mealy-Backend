from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency / Helper to get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
