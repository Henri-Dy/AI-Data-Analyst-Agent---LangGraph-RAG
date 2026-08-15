"""Business documents (RAG) management: upload a document, list ingested
documents, or delete one. Complements the CLI-only `scripts/ingest_documents.py`
path with an in-app equivalent for user-supplied documents.
"""
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from langchain_core.embeddings import Embeddings
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.models.rag_documents import RagDocument
from app.database.session import get_db
from app.models.documents import DocumentSummary, DocumentUploadResponse
from app.rag.embeddings import get_embeddings
from app.rag.ingest import ingest_document
from app.rag.loader import BusinessDocument

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    title: str = Form(...),
    category: str = Form(...),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db),
    embeddings: Embeddings = Depends(get_embeddings),
) -> DocumentUploadResponse:
    raw = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_upload_size_mb}MB upload limit"
        )

    content = raw.decode("utf-8", errors="replace").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    document = BusinessDocument(
        title=title, category=category, content=content, source_path=f"upload:{file.filename}"
    )
    document_id = uuid.uuid4()
    chunks_created = ingest_document(session, embeddings, document, document_id=document_id)
    return DocumentUploadResponse(document_id=document_id, chunks_created=chunks_created)


@router.get("", response_model=list[DocumentSummary])
def list_documents(session: Session = Depends(get_db)) -> list[DocumentSummary]:
    rows = session.execute(
        select(
            RagDocument.document_id,
            RagDocument.title,
            RagDocument.category,
            func.count(RagDocument.id),
            func.min(RagDocument.created_at),
        )
        .where(RagDocument.document_id.is_not(None))
        .group_by(RagDocument.document_id, RagDocument.title, RagDocument.category)
        .order_by(func.min(RagDocument.created_at).desc())
    ).all()

    return [
        DocumentSummary(
            document_id=document_id,
            title=title,
            category=category,
            chunk_count=chunk_count,
            created_at=created_at,
        )
        for document_id, title, category, chunk_count, created_at in rows
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, session: Session = Depends(get_db)) -> None:
    deleted = session.query(RagDocument).filter(RagDocument.document_id == document_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    session.commit()
