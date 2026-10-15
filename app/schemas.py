
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# E.164 format: + country code + number, e.g. +919876543210
PHONE_PATTERN = r"^\+[1-9]\d{7,14}$"

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

class UserRead(BaseModel):
    """Schema for reading user information."""
    model_config = ConfigDict(extra="forbid")
    id: int
    phone_number: str
    created_at: datetime
    updated_at: datetime