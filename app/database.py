import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# In production (Render, Railway, etc.) set DATABASE_URL to your Postgres
# connection string and this picks it up automatically. Locally, with no
# DATABASE_URL set, it falls back to a SQLite file so you can still run
# everything with zero setup.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./afb.db")

# Render/Railway sometimes hand out "postgres://" URLs; SQLAlchemy 2.x wants
# "postgresql://" — normalize it so both work without a manual fix.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
