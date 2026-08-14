"""pgvector-backed similarity search over ingested business documents."""
from dataclasses import dataclass

from langchain_core.embeddings import Embeddings
from sqlalchemy.orm import Session

from app.database.models.rag_documents import RagDocument


@dataclass
class RetrievedChunk:
    title: str
    category: str
    content: str
    source_path: str
    distance: float


def retrieve(
    session: Session,
    embeddings: Embeddings,
    query: str,
    top_k: int = 5,
    category: str | None = None,
) -> list[RetrievedChunk]:
    """Returns the top_k business-document chunks most relevant to `query`.

    Uses pgvector cosine distance (lower is more similar). RAG supplies
    business context for interpretation only — it never replaces SQL for
    querying tabular data.
    """
    query_vector = embeddings.embed_query(query)

    stmt = session.query(
        RagDocument, RagDocument.embedding.cosine_distance(query_vector).label("distance")
    )
    if category:
        stmt = stmt.filter(RagDocument.category == category)
    rows = stmt.order_by("distance").limit(top_k).all()

    return [
        RetrievedChunk(
            title=doc.title,
            category=doc.category,
            content=doc.content,
            source_path=doc.doc_metadata.get("source_path", ""),
            distance=float(distance),
        )
        for doc, distance in rows
    ]
