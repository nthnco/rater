from datetime import datetime

from sqlalchemy import CHAR, BigInteger, DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.movie import StreamingService


class User(Base):
    """An account. Email is stored lowercased so lookups are case-insensitive (DESIGN.md §6)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(CHAR(2), server_default=text("'US'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    services: Mapped[list[StreamingService]] = relationship(
        secondary="user_services", order_by=StreamingService.name
    )


class UserService(Base):
    """Join table: which streaming services a user has (many-to-many)."""

    __tablename__ = "user_services"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("streaming_services.id"), primary_key=True
    )
