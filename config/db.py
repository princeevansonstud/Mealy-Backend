"""SQLAlchemy engine and request-scoped session helpers."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Yield a session for scripts and non-request callers."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class SQLAlchemySessionMiddleware:
    """Attach one SQLAlchemy transaction to each HTTP request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.db = SessionLocal()
        try:
            response = self.get_response(request)
            if response.status_code < 400:
                request.db.commit()
            else:
                request.db.rollback()
            return response
        except Exception:
            request.db.rollback()
            raise
        finally:
            request.db.close()
