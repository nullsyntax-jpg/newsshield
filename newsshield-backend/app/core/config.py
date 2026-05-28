from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://newsshield.vercel.app",
    ]

    # ── Data paths ───────────────────────────────────────────────────────────
    GDELT_OUTPUT_DIR: str = "../gdelt_output"
    MODEL_DIR: str = "../src"

    # ── External APIs ────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    RESEND_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()