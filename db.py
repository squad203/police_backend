from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"postgresql+pg8000://postgres:MyPassDrona@146.190.9.62:3306/BGdata"

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=500,
    pool_timeout=30,
    max_overflow=10,
    echo=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
