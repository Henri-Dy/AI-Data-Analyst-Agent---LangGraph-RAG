"""Exercises /api/documents end to end (upload -> list -> delete) against
the real local Postgres instance, with a fake embedder injected via
dependency override so no real LLM/embedding API key is required.
"""
import pytest
from fastapi.testclient import TestClient
from langchain_community.embeddings import DeterministicFakeEmbedding

from app.database.models.rag_documents import EMBEDDING_DIM
from app.rag.embeddings import get_embeddings
from main import app


@pytest.fixture(autouse=True)
def _fake_embeddings():
    app.dependency_overrides[get_embeddings] = lambda: DeterministicFakeEmbedding(size=EMBEDDING_DIM)
    yield
    app.dependency_overrides.pop(get_embeddings, None)


def test_upload_list_and_delete_a_document():
    with TestClient(app) as client:
        upload = client.post(
            "/api/documents",
            data={"title": "Test Policy", "category": "test_fixture"},
            files={"file": ("policy.md", b"Refunds are processed within 14 days.", "text/markdown")},
        )
        assert upload.status_code == 200
        document_id = upload.json()["document_id"]
        assert upload.json()["chunks_created"] >= 1

        listing = client.get("/api/documents")
        assert listing.status_code == 200
        ids = [d["document_id"] for d in listing.json()]
        assert document_id in ids

        delete = client.delete(f"/api/documents/{document_id}")
        assert delete.status_code == 204

        listing_after = client.get("/api/documents")
        ids_after = [d["document_id"] for d in listing_after.json()]
        assert document_id not in ids_after


def test_delete_unknown_document_returns_404():
    with TestClient(app) as client:
        response = client.delete("/api/documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_upload_oversized_document_returns_413(monkeypatch):
    from app.core.config import Settings

    tiny_settings = Settings(max_upload_size_mb=0)
    from app.core.config import get_settings

    app.dependency_overrides[get_settings] = lambda: tiny_settings
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents",
                data={"title": "Too Big", "category": "test_fixture"},
                files={"file": ("big.md", b"x" * 1024, "text/markdown")},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)
    assert response.status_code == 413
