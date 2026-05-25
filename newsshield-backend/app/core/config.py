from pydantic_settings import BaseSettings,SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────────
    # In dev: allow all localhost ports so Member B can use any Vite/CRA port.
    # Override in .env for staging/prod with the real Vercel/Netlify URL.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://newsshield.vercel.app",   # update when Member B deploys
    ]

    # ── Data paths ───────────────────────────────────────────────────────────
    GDELT_OUTPUT_DIR: str = "../gdelt_output"
    MODEL_DIR: str = "../src"

    # ── External APIs ────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()