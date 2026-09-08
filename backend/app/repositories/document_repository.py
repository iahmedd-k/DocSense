from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        filename: str,
        storage_key: str,
        mime_type: str,
        file_size: int,
        status: DocumentStatus = DocumentStatus.PENDING,
    ) -> Document:

        document = Document(
            user_id=user_id,
            filename=filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=file_size,
            status=status,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_by_id(self, document_id: int) -> Document | None:
        statement = select(Document).where(Document.id == document_id)

        return self.db.scalar(statement)

    def get_by_id_and_user(
        self,
        document_id: int,
        user_id: int,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )

        return self.db.scalar(statement)

    def list_by_user(self, user_id: int) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )

        return list(self.db.scalars(statement))

    def update_status(
        self,
        document: Document,
        status: DocumentStatus,
    ) -> Document:
        document.status = status
        self.db.commit()
        self.db.refresh(document)

        return document