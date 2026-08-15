"""Exercises /api/datasets end to end (upload -> list -> delete) against the
real local Postgres instance, and confirms the Schema Agent picks up an
uploaded table automatically with no extra wiring.
"""
from fastapi.testclient import TestClient

from app.agents.schema_agent import inspect_schema
from app.database.session import engine
from main import app

CSV_BYTES = b"product,revenue\nWidget,100\nGadget,250\n"


def test_upload_list_and_delete_a_dataset():
    with TestClient(app) as client:
        upload = client.post(
            "/api/datasets",
            data={"table_name": "test_upload_widgets"},
            files={"file": ("widgets.csv", CSV_BYTES, "text/csv")},
        )
        assert upload.status_code == 200
        body = upload.json()
        assert body["table_name"] == "test_upload_widgets"
        assert body["row_count"] == 2
        assert body["columns"] == ["product", "revenue"]

        assert "test_upload_widgets" in inspect_schema(engine)

        listing = client.get("/api/datasets")
        assert any(d["table_name"] == "test_upload_widgets" for d in listing.json())

        delete = client.delete("/api/datasets/test_upload_widgets")
        assert delete.status_code == 204

    assert "test_upload_widgets" not in inspect_schema(engine)


def test_upload_with_reserved_table_name_returns_400():
    with TestClient(app) as client:
        response = client.post(
            "/api/datasets",
            data={"table_name": "orders"},
            files={"file": ("orders.csv", CSV_BYTES, "text/csv")},
        )
    assert response.status_code == 400


def test_delete_untracked_table_returns_404():
    with TestClient(app) as client:
        response = client.delete("/api/datasets/not_a_real_dataset")
    assert response.status_code == 404
