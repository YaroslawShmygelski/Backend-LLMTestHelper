from sqlalchemy.orm import mapped_column, Mapped
from app.database.postgres_config import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)