"""Unit-tests `ingest_document` (app/rag/ingest.py) directly with a fake
embedder, against the real local Postgres/pgvector instance, verifying it
groups all chunks of one document under the same document_id.
"""
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.database.models.rag_documents import EMBEDDING_DIM, RagDocument
from app.rag.ingest import ingest_document
from app.rag.loader import BusinessDocument

LONG_CONTENT = " ".join(f"Sentence number {i} about revenue." for i in range(200))


def test_ingest_document_tags_every_chunk_with_the_same_document_id(db_session):
    embeddings = DeterministicFakeEmbedding(size=EMBEDDING_DIM)
    document = BusinessDocument(
        title="Uploaded Doc", category="test_fixture", content=LONG_CONTENT, source_path="upload:test.md"
    )

    chunks_created = ingest_document(db_session, embeddings, document)
    try:
        assert chunks_created > 1  # long content should split into multiple chunks

        rows = db_session.query(RagDocument).filter(RagDocument.title == "Uploaded Doc").all()
        assert len(rows) == chunks_created
        document_ids = {row.document_id for row in rows}
        assert len(document_ids) == 1
        assert all(row.document_id is not None for row in rows)
    finally:
        db_session.query(RagDocument).filter(RagDocument.title == "Uploaded Doc").delete()
        db_session.commit()


def test_ingest_document_returns_zero_for_empty_content(db_session):
    embeddings = DeterministicFakeEmbedding(size=EMBEDDING_DIM)
    document = BusinessDocument(title="Empty", category="test_fixture", content="", source_path="upload:empty.md")

    assert ingest_document(db_session, embeddings, document) == 0
