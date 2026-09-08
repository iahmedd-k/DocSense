from datetime import datetime

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_numbers: Mapped[list] = mapped_column(
        sa.JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
        default=list,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        sa.JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
        default=dict,
    )

    embedding = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=False,
    )

    # PostgreSQL generated column (see migration 0006) holding the tsvector for
    # full-text search over ``content``. It is maintained entirely by the
    # database; the application never writes to it. A SQLite fallback type is
    # provided so the ORM model works in tests using the SQLite dialect.
    search_vector = mapped_column(
        TSVECTOR().with_variant(sa.Text(), "sqlite"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )