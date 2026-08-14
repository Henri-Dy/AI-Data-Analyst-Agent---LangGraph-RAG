"""End-to-end RAG ingestion: load -> chunk -> embed -> store in pgvector.

The embeddings instance is injected rather than constructed internally so
tests can supply a deterministic fake embedder without calling a real LLM
provider (see tests/test_rag_retriever.py).
"""
from pathlib import Path

from langchain_core.embeddings import Embeddings
from sqlalchemy.orm import Session

from app.database.models.rag_documents import RagDocument
from app.rag.chunking import chunk_documents
from app.rag.loader import DEFAULT_DOCS_DIR, load_documents


def ingest_documents(
    session: Session,
    embeddings: Embeddings,
    docs_dir: Path = DEFAULT_DOCS_DIR,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> int:
    """Ingests all business documents into `rag_documents`. Returns chunk count."""
    documents = load_documents(docs_dir)
    chunks = chunk_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return 0

    vectors = embeddings.embed_documents([chunk.content for chunk in chunks])

    rows = [
        RagDocument(
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
