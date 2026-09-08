from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: int,
        user_id: int,
        page_number: int,
        page_numbers: list[int],
        content: str,
        content_type: str,
        metadata: dict,
        embedding: list[float],
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            user_id=user_id,
            page_number=page_number,
            page_numbers=page_numbers,
            content=content,
            content_type=content_type,
            metadata_=metadata,
            embedding=embedding,
        )

        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)

        return chunk

    def create_many(
        self,
        chunks: list[dict],
    ) -> list[DocumentChunk]:
        models = [
            DocumentChunk(
                document_id=chunk["document_id"],
                user_id=chunk["user_id"],
                page_number=chunk["page_number"],
                page_numbers=chunk["page_numbers"],
                content=chunk["content"],
                content_type=chunk["content_type"],
                metadata_=chunk["metadata"],
                embedding=chunk["embedding"],
            )
            for chunk in chunks
        ]
        self.db.add_all(models)
        self.db.commit()
        for model in models:
            self.db.refresh(model)

        return models

    def list_by_document(
        self,
        document_id: int,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.id)
        )

        return list(self.db.scalars(statement))

    def list_by_user(
        self,
        user_id: int,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.user_id == user_id)
            .order_by(DocumentChunk.id)
        )

        return list(self.db.scalars(statement))

    def delete_by_document(self, document_id: int) -> None:
        statement = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )
        for chunk in self.db.scalars(statement):
            self.db.delete(chunk)
        self.db.commit()

    def count_by_document(self, document_id: int) -> int:
        statement = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )
        return len(list(self.db.scalars(statement)))
