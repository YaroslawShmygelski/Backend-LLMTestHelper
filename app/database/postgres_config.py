import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

DeclarativeBase = declarative_base()

postgres_db_engine = create_async_engine(
    f"postgresql+asyncpg://{os.getenv('POSTGRES_DB_USER')}:{os.getenv('POSTGRES_DB_PASSWORD')}"
    f"@{os.getenv('POSTGRES_DB_HOST')}:{os.getenv('POSTGRES_DB_PORT')}/{os.getenv('POSTGRES_DB_NAME')}"
)

async_postgres_session = async_sessionmaker(
    bind=postgres_db_engine, expire_on_commit=False
)


async def get_async_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_postgres_session() as session:
        yield session
