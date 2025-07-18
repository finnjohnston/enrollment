import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from core.exceptions import DatabaseError
from db.models.base import Base
from config.config import DATABASE_URL

from contextlib import contextmanager

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(engine)

@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        session.close()

# Example usage:
# with db_session() as session:
#     session.add(obj)
#     ... 