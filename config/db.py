import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class SQLAlchemySessionMiddleware:
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
