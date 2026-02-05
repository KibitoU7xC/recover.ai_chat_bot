# config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Security: Never default to a real key in code.
    # If key is missing, the app will refuse to start (Fail Fast).
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "models/gemini-3-flash-preview"

    # API Security for your friend
    API_SECRET_TOKEN: str

    class Config:
        env_file = ".env"


settings = Settings()