import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@127.0.0.1:3306/clear_termite_db")

# Setup SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=engine)
    logging.info("Database reflection complete. Tables loaded.")
except Exception as e:
    logging.error(f"Failed to connect to database: {e}")
    engine = None
    SessionLocal = None
    metadata = None

def get_db():
    if not SessionLocal:
        raise Exception("Database connection not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
