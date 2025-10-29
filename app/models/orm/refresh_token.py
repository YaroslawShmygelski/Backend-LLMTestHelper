from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.postgres_config import DeclarativeBase
from app.models.orm.mixin import MixinModel


# pylint: disable=too-few-public-methods
class RefreshToken(DeclarativeBase, MixinModel):
    __tablename__ = "refresh_token"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_agent: Mapped[str] = mapped_column(nullable=True)
    ip_address: Mapped[str] = mapped_column(nullable=True)
    revoked: Mapped[bool] = mapped_column(nullable=True, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
