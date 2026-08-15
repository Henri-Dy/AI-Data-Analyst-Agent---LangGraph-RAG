"""End-to-end RAG ingestion: load -> chunk -> embed -> store in pgvector.

The embeddings instance is injected rather than constructed internally so
tests can supply a deterministic fake embedder without calling a real LLM
provider (see tests/test_rag_retriever.py).
"""
import uuid
from pathlib import Path

from langchain_core.embeddings import Embeddings
from sqlalchemy.orm import Session

from app.database.models.rag_documents import RagDocument
from app.rag.chunking import chunk_documents
from app.rag.loader import DEFAULT_DOCS_DIR, BusinessDocument, load_documents


def ingest_document(
    session: Session,
    embeddings: Embeddings,
    document: BusinessDocument,
    document_id: uuid.UUID | None = None,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> int:
    """Chunks, embeds, and stores a single `BusinessDocument`, tagging every
    resulting chunk with the same `document_id` so it can be listed/deleted
    as a unit later. Returns the chunk count."""
    chunks = chunk_documents([document], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return 0

    document_id = document_id or uuid.uuid4()
    vectors = embeddings.embed_documents([chunk.content for chunk in chunks])

    rows = [
        RagDocument(
            document_id=document_id,
            title=chunk.title,
            category=chunk.category,
            content=chunk.content,
            doc_metadata={"source_path": chunk.source_path, "chunk_index": chunk.chunk_index},
            embedding=vector,
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    session.add_all(rows)
    session.commit()
    return len(rows)


def ingest_documents(
    session: Session,
    embeddings: Embeddings,
    docs_dir: Path = DEFAULT_DOCS_DIR,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> int:
    """Ingests all business documents into `rag_documents`. Returns chunk count."""
    documents = load_documents(docs_dir)
    total = 0
    for document in documents:
        total += ingest_document(
            session, embeddings, document, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    return total
