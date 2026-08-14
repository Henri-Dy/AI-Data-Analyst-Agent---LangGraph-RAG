"""Tests the pgvector storage/retrieval round-trip using a deterministic fake
embedder, so the test suite never calls a paid LLM provider. Retrieval
*ranking quality* still depends on a real embedding model in production;
this test only verifies the plumbing (store -> cosine search -> get back
the right row) against the real local Postgres + pgvector instance.
"""
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.database.models.rag_documents import EMBEDDING_DIM, RagDocument
from app.rag.retriever import retrieve

TEST_CATEGORY = "test_fixture"

FIXTURE_DOCS = [
    ("Doc A", "The quarterly revenue report covers North America and Europe."),
    ("Doc B", "The discount policy caps standard promotions at thirty percent."),
    ("Doc C", "APAC enterprise demand is the most volatile segment month to month."),
]


def _insert_fixtures(session, embeddings):
    rows = [
        RagDocument(
            title=title,
            category=TEST_CATEGORY,
            content=content,
            doc_metadata={"source_path": "test", "chunk_index": 0},
            embedding=embeddings.embed_query(content),
        )
        for title, content in FIXTURE_DOCS
    ]
    session.add_all(rows)
    session.commit()
    return rows


def test_retrieve_returns_the_matching_chunk_first(db_session):
    embeddings = DeterministicFakeEmbedding(size=EMBEDDING_DIM)
    rows = _insert_fixtures(db_session, embeddings)
    try:
        target_content = FIXTURE_DOCS[2][1]
        results = retrieve(
            db_session, embeddings, query=target_content, top_k=2, category=TEST_CATEGORY
        )

        assert len(results) == 2
        assert results[0].title == "Doc C"
        assert results[0].distance < 1e-6
    finally:
        for row in rows:
            db_session.delete(row)
        db_session.commit()


def test_retrieve_respects_category_filter(db_session):
    embeddings = DeterministicFakeEmbedding(size=EMBEDDING_DIM)
    rows = _insert_fixtures(db_session, embeddings)
    try:
        results = retrieve(
            db_session, embeddings, query="anything", top_k=10, category="does_not_exist"
        )
        assert results == []
    finally:
        for row in rows:
            db_session.delete(row)
        db_session.commit()
