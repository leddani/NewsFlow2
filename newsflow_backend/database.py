"""
Database configuration for NewsFlow AI Editor.

This module defines the SQLAlchemy engine, session factory and declarative
base for the application. By default it uses SQLite for ease of
development, but any database supported by SQLAlchemy (PostgreSQL,
MySQL, etc.) can be configured via the `DATABASE_URL` environment
variable. When using SQLite the `check_same_thread` option is set to
allow interaction from multiple threads (as is typical with FastAPI).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read database connection string from environment or fall back to SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./newsflow.db")

# Configure engine with appropriate connection args for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()