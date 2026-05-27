"""
Base declarative model for SQLAlchemy ORM.
All models inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
