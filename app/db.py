from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .config import get_settings

settings = get_settings()

# Async engine using asyncpg
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql+psycopg", "postgresql+asyncpg"),
    echo=True,  # logs SQL queries, you can disable in prod
    future=True,
)

# Async session
AsyncSessionLocal = sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def ping_db() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
