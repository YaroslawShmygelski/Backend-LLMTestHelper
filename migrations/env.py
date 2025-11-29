import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

from app.database.postgres_config import DeclarativeBase
from dotenv import load_dotenv

from app.database.models.orm.test_run import TestRun
from app.database.models.orm.user import User
from app.database.models.orm.test import Test
from app.database.models.orm.refresh_token import RefreshToken
from app.database.models.orm.document import Document
from app.database.models.orm.document_embedding import DocumentEmbedding

load_dotenv()
# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Generate the DB URL from environment variables."""
    user = os.getenv("POSTGRES_DB_USER")
    password = os.getenv("POSTGRES_DB_PASSWORD")
    host = os.getenv("POSTGRES_DB_HOST")
    port = os.getenv("POSTGRES_DB_PORT")
    dbname = os.getenv("POSTGRES_DB_NAME")

    # Use synchronous psycopg2 driver for Alembic
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


config.set_main_option("sqlalchemy.url", get_url())

# Import your models here
# from app.models import Base
# target_metadata = Base.metadata
target_metadata = DeclarativeBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode (generate SQL)."""
    url = get_url()  # call the function!

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine offline/online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
