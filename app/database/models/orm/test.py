from pydantic import BaseModel
from sqlalchemy import ForeignKey, TypeDecorator, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.postgres_config import DeclarativeBase
from app.database.models.orm.mixin import MixinModel
from app.schemas.tests.test import TestQuestions


# pylint: disable=too-few-public-methods
# pylint: disable=not-callable
class PydanticJSON(TypeDecorator):
    impl = JSON

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_class = model_class

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.model_class(**value)


class Test(DeclarativeBase, MixinModel):
    __tablename__ = "tests"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    type: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[TestQuestions] = mapped_column(
        PydanticJSON(TestQuestions), nullable=False
    )
    is_submitted: Mapped[bool] = mapped_column(nullable=False, default=False)
