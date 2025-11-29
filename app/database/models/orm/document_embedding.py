from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.database.models.orm.mixin import MixinModel
from app.database.postgres_config import DeclarativeBase

class DocumentEmbedding(DeclarativeBase, MixinModel):
    __tablename__ = "document_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"),
                                             nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    document = relationship("Document", back_populates="embeddings")
