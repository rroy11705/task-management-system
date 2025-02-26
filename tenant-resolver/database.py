import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL")

# Store dynamically created database engines
engines = {}

def get_engine(db_url):
    """Get or create an SQLAlchemy engine for a given database URL."""
    if db_url not in engines:
        engines[db_url] = create_engine(db_url)
    return engines[db_url]

def get_db(db_url):
    """Yield a new session for the given tenant-specific database."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine(db_url))
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
