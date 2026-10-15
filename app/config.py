from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://appuser:changeme@localhost:5432/appdb"
    envirement: str = "development"  # "development" or "production"
    public_base_url: str = "http://localhost:8000"

    # JWT settings
    jwt_secret_key: str = "DC_tasgraIPEEr0EW2dH9D42nD0EBXoR3Y2fGElAVrCu2miKizWW7_a0GklfjxRg"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # OTP 
    otp_length: int = 6
    otp_expire_minutes: int = 5
    otp_max_attempts: int = 5             # wrong guesses allowed before the OTP is invalidated
    otp_max_requests_per_window: int = 3  # max OTP requests allowed per phone number in a time window
    otp_request_window_minutes: int = 10  # time window for OTP request limit

    # Profile pictures
    media_dir: str = "media"
    avatar_max_bytes: int = 5 * 1024 * 1024  # 5 MB
    avatar_size_px: int = 512



settings = Settings()