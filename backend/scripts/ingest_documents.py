"""Ingests data/business_docs into pgvector using the configured embedding provider.

Run with: python scripts/ingest_documents.py
Requires OPENAI_API_KEY (or GOOGLE_API_KEY, if EMBEDDING_PROVIDER=gemini) in
backend/.env, and the database schema to already be migrated.
"""
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal, engine  # noqa: E402
from app.rag.embeddings import get_embeddings  # noqa: E402
from app.rag.ingest import ingest_documents  # noqa: E402


def main() -> None:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE rag_documents RESTART IDENTITY"))

    session = SessionLocal()
    try:
        embeddings = get_embeddings()
        count = ingest_documents(session, embeddings)
        print(f"Ingested {count} chunks into rag_documents.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
