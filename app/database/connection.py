import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

database_url = settings.DATABASE_URL
turso_token = os.getenv("TURSO_AUTH_TOKEN")

connect_args = {}

if database_url.startswith("libsql://") or database_url.startswith("sqlite+libsql://"):
    if database_url.startswith("libsql://"):
        database_url = database_url.replace("libsql://", "sqlite+libsql://", 1)
    if turso_token:
        connect_args["auth_token"] = turso_token
elif database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
