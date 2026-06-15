#!/usr/bin/env python3
"""
RUT_TRAILBLAZER Database Configuration
Sets up SQLite database connection and session management using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL for local SQLite instance
SQLALCHEMY_DATABASE_URL = "sqlite:///./rut_trailblazer.db"

# Create engine
# connect_args={"check_same_thread": False} is required only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

def get_db():
    """
    Dependency helper to yield database session and close it afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
