"""Database setup with SQLAlchemy ORM and asyncpg."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.config import settings

logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Document(Base):
    """Document table model."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    search_vector: Mapped[TSVECTOR | None] = mapped_column(
        TSVECTOR, nullable=True, index=True, default=None
    )

    # Relationship to versions
    versions: Mapped[list["Version"]] = relationship(
        "Version",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(Version.version_number)",
    )

    # Relationship to references (documents that reference this document)
    referencing_documents: Mapped[list["DocumentReference"]] = relationship(
        "DocumentReference",
        back_populates="referenced_document",
        foreign_keys="DocumentReference.referenced_document_id",
        cascade="all, delete-orphan",
    )

    # Relationship to references (documents that this document references)
    referenced_documents: Mapped[list["DocumentReference"]] = relationship(
        "DocumentReference",
        back_populates="source_document",
        foreign_keys="DocumentReference.source_document_id",
        cascade="all, delete-orphan",
    )


class Version(Base):
    """Version table model."""

    __tablename__ = "versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship to document
    document: Mapped[Document] = relationship("Document", back_populates="versions")


class DocumentReference(Base):
    """Model to track references between documents."""

    __tablename__ = "document_references"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "referenced_document_id",
            "reference_text",
            name="uq_document_reference",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    source_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referenced_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reference_text: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), default="inline", nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source_document: Mapped[Document] = relationship(
        "Document", back_populates="referenced_documents", foreign_keys=[source_document_id]
    )
    referenced_document: Mapped[Document] = relationship(
        "Document", back_populates="referencing_documents", foreign_keys=[referenced_document_id]
    )


# Async engine and session factory

engine = create_async_engine(settings.postgres_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add search_vector column to existing documents table if it doesn't exist
        try:
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("""
                    ALTER TABLE documents
                    ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
                    """)
                )
            )
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_documents_search_vector ON documents USING GIN(search_vector)"
                    )
                )
            )
        except Exception as e:
            logger.warning(f"Could not add search_vector column: {e}")

        # Add extracted_text column to versions table for text extraction
        try:
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("""
                    ALTER TABLE versions
                    ADD COLUMN IF NOT EXISTS extracted_text TEXT
                    """)
                )
            )
        except Exception as e:
            logger.warning(f"Could not add extracted_text column: {e}")

        # Create document_references table
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass

        logger.info("Database tables created successfully")
