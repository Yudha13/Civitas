"""Database configuration for CIVITAS persistence."""
from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./civitas.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
class Base(DeclarativeBase):
    """Base class for CIVITAS ORM models."""
def get_session():
    session = SessionLocal()
    try: yield session
    finally: session.close()
