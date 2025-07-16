import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.base import Base

DB_USER = os.getenv('POSTGRES_USER', 'finnjohnston')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Ricknash2019!')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'enrollment')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(engine) 