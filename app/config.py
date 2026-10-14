from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://appuser:changeme@localhost:5432/appdb"


settings = Settings()