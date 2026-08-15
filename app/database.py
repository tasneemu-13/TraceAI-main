from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import settings

# Create engine for MySQL connection
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=3600
)

# Configure session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread-safety (especially for NiceGUI or tasks running in worker threads)
db_session = scoped_session(SessionLocal)

# Base class for declarative SQLAlchemy models
Base = declarative_base()

# Dependency to retrieve a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
