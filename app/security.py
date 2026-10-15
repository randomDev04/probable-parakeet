import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt


from app.config import settings

def utcnow() -> datetime:
    """Return the current UTC time with timezone information."""
    return datetime.now(timezone.utc)

def as_utc(dt: datetime) -> datetime:
    """Some DB derivers return naive datetimes; treat them as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

# ---- OTPs and refersh tokens; random values, stored only as HMAC hashes ----

def generate_otp() -> str:
    """Generate a random 6 digit OTP code."""
    n = settings.otp_length
    return f"{secrets.randbelow(10**n):0{n}d}"

def generate_refresh_token() -> str:
    """Generate a random refresh token."""
    return secrets.token_urlsafe(48)

def hash_value(value: str) -> str:
    """Return a HMAC hash of the given value using the JWT secret key."""
    return hmac.new(settings.jwt_secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()

def verify_hash(value: str, hashed: str) -> bool:
    """Verify that the given value matches the given HMAC hash."""
    return hmac.compare_digest(hash_value(value), hashed)

# ---- JWT access tokens ---- 

def create_access_token(user_id: uuid.UUID) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp":  now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError if the token is invalid, expired or tampered with."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return payload