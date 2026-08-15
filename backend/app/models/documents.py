"""Schemas for the business documents (RAG) management API."""
import datetime
import uuid

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    document_id: uuid.UUID
    title: str
    category: str
    chunk_count: int
    created_at: datetime.datetime


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    chunks_created: int
