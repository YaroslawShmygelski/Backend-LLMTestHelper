from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


# pylint: disable=too-few-public-methods
# pylint: disable=not-callable
class MixinModel:
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
