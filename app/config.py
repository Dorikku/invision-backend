import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENV: str = os.getenv("ENV", "dev")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/sales_db",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
