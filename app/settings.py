from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


# pylint: disable=too-few-public-methods
class PostgresDBSettings(BaseSettings):
    ENV: str = "dev"
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


postgres_db_settings = PostgresDBSettings()
