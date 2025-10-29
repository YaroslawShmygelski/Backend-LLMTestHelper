from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column, Mapped
from app.database.postgres_config import DeclarativeBase
from app.models.orm.mixin import MixinModel


# pylint: disable=too-few-public-methods
class User(DeclarativeBase, MixinModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True)
    phone_number: Mapped[int] = mapped_column(unique=True)
    country_code: Mapped[int] = mapped_column()
    is_premium: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[str] = mapped_column()
    ip_address: Mapped[str] = mapped_column(nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
