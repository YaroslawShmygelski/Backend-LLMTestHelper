import os

from fastapi.openapi.utils import get_openapi
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

LOGGING_LEVEL: str = "DEBUG"
MAX_PARALLEL_TASKS = 9
ENV: str = os.getenv("ENV", "prod")

TEST_RUNS_JOBS_STORAGE = {}

UPLOAD_DOCUMENT_JOBS_STORAGE = {}
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5 MB
PDF_DOCUMENT_TYPE, TXT_DOCUMENT_TYPE = "application/pdf", "text/plain"
ALLOWED_DOCUMENT_TYPES = [PDF_DOCUMENT_TYPE, TXT_DOCUMENT_TYPE]
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 50
EMBEDDING_DIM = 3072


class PostgresDBSettings(BaseSettings):
    ENV: str = ENV
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    DATABASE_URL: PostgresDsn | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FastAPI application",
        version="1.0.0",
        description="JWT Authentication and Authorization",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema
