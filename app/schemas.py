import uuid
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from app.config import settings
from app.constants import normalize_state

# E.164 format: + country code + number, e.g. +919876543210
PHONE_PATTERN = r"^\+[1-9]\d{7,14}$"
MIN_AGE = 13
MAX_AGE = 120

def calulate_age(dob:date, today:date | None = None) -> int:
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# ------------- Auth ---------------

class OTPRequest(BaseModel):
    """Schema for OTP request."""
    model_config = ConfigDict(extra="forbid")
    phone_number: str = Field(..., pattern=PHONE_PATTERN, examples=["+919876543210"], description="The phone number to which the OTP will be sent.")


class OTPVerify(BaseModel):
    """Schema for OTP verification."""
    model_config = ConfigDict(extra="forbid")
    phone_number: str = Field(..., pattern=PHONE_PATTERN, examples=["+919876543210"], description="The phone number to which the OTP was sent.")
    otp: str = Field(..., pattern=r"^\d{4,8}$", examples=["123456"], description="The OTP to verify.")

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token:str
    refresh_token:str
    token_type:str = "bearer"
    expires_int: int # seconds until the access token expires


class RefreshRequest(BaseModel):
    """Schema for refresh token request."""
    model_config = ConfigDict(extra="forbid")
    refresh_token:str


# ------------- User profile ---------------

class UserRead(BaseModel):
    """Schema for reading user information."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    phone_number: str
    name: str | None
    date_of_birth: date |None
    state: str | None
    avatar_key: str | None = Field(default=None, exclude=True) # internal only
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def age(self)-> int | None:
        return calulate_age(self.date_of_birth) if self.date_of_birth else None

    @computed_field
    @property
    def profile_pic_url(self) -> str | None:
        if not self.avatar_key:
            return None
        return f"{settings.public_base_url.rstrip("/")}/media/avatars/{self.avatar_key}"

    @computed_field
    @property
    def profile_complete(self) -> bool:
        return bool(self.name and self.date_of_birth and self.state)


class UserUpdate(BaseModel):
    """"PATCH body: send only the fileds want to change. Send null to clear one."""

    model_config  = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, examples=["Jhon Sian"])
    date_of_birth: date | None = Field(default=None, examples=["2001-04-23"])
    state: str | None = Field(default=None, examples=["Himachal Pradesh"])

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = " ".join(v.split()) # trim and collapse extra spaces
        if not 1 <= len(v) <= 100:
            raise ValueError("Name must be 1 to 100 charachters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is None:
            return v
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        age = calulate_age(v)
        if age < MIN_AGE:
            raise ValueError(f"Your must be at least {MIN_AGE} years old")
        if age > MAX_AGE:
            raise ValueError("Please enter a valud date of birth")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        if v is None:
            return v
        normalized = normalize_state(v)
        if not normalized:
            raise ValueError("Unknown state. Get valid options from GET /meta/states")
        return normalized
        