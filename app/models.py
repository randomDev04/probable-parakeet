import uuid
from datetime import datetime, date, timezone

from sqlalchemy import Date, Integer, String, DateTime, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

def utcnow() -> datetime:
    """Return the current UTC time with timezone information."""
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id:Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number:Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Profile (all optional: filled in after first login)
    name: Mapped[str | None] = mapped_column(String(100), default=None)
    date_of_birth: Mapped[date | None] = mapped_column(Date, default=None)
    state: Mapped[str | None] = mapped_column(String(60), default=None)
    avatar_key:Mapped[str | None] = mapped_column(String(100), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id:Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)