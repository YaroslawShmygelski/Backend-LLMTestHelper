import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.postgres_config import DeclarativeBase
from app.models.orm.mixin import MixinModel
from app.models.orm.test import PydanticJSON
from app.schemas.test import AnsweredTestContent


class TestRun(DeclarativeBase, MixinModel):
    __tablename__ = "test_runs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    llm_model: Mapped[str] = mapped_column(nullable=True)
    llm_prompt_tokens: Mapped[int] = mapped_column(nullable=True)
    llm_completion_tokens: Mapped[int] = mapped_column(nullable=True)
    llm_answering_time: Mapped[float] = mapped_column(nullable=True)
    run_content: Mapped[AnsweredTestContent] = mapped_column(
        PydanticJSON(AnsweredTestContent), nullable=False
    )
    submitted_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    job_id: Mapped[str] = mapped_column(nullable=False)
