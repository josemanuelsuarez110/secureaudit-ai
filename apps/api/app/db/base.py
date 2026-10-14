"""Base declarativa para todos los modelos."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base común para todos los modelos SQLAlchemy."""

    pass
