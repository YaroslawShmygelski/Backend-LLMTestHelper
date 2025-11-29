from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.models.orm.mixin import MixinModel
from app.database.postgres_config import DeclarativeBase
from app.database.models.orm.document_embedding import DocumentEmbedding

class Document(DeclarativeBase, MixinModel):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(nullable=False)
    original_file_name: Mapped[str] = mapped_column(nullable=False)
    file_type: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    scope: Mapped[str] = mapped_column(nullable=False, server_default="test")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), index=True)

    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(
        "DocumentEmbedding",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )