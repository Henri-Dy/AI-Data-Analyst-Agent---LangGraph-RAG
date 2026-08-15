"""Tabular datasets management: upload a CSV as a new queryable table, list
uploaded datasets, or delete one. New tables are picked up automatically by
the Schema Agent (`app/agents/schema_agent.py::inspect_schema`) with no
further wiring, since it enumerates `information_schema` dynamically.
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.models.uploaded_datasets import UploadedDataset
from app.database.session import engine, get_db
from app.models.datasets import DatasetSummary, DatasetUploadResponse
from app.tools.dataset_loader import DatasetTableError, create_table_from_csv, drop_uploaded_table, sanitize_table_name

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile,
    table_name: str | None = Form(None),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db),
) -> DatasetUploadResponse:
    raw = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_upload_size_mb}MB upload limit"
        )

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}") from e

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV has no rows")

    name = sanitize_table_name(table_name or file.filename or "dataset")

    try:
        row_count = create_table_from_csv(engine, df, name)
    except DatasetTableError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    columns = list(df.columns.astype(str))
    session.add(
        UploadedDataset(
            table_name=name, original_filename=file.filename or name, row_count=row_count, columns=columns
        )
    )
    session.commit()
    return DatasetUploadResponse(table_name=name, row_count=row_count, columns=columns)


@router.get("", response_model=list[DatasetSummary])
def list_datasets(session: Session = Depends(get_db)) -> list[DatasetSummary]:
    rows = session.query(UploadedDataset).order_by(UploadedDataset.created_at.desc()).all()
    return [
        DatasetSummary(
            table_name=row.table_name,
            original_filename=row.original_filename,
            row_count=row.row_count,
            columns=row.columns,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.delete("/{table_name}", status_code=204)
def delete_dataset(table_name: str, session: Session = Depends(get_db)) -> None:
    row = session.query(UploadedDataset).filter(UploadedDataset.table_name == table_name).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        drop_uploaded_table(engine, table_name)
    except DatasetTableError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    session.delete(row)
    session.commit()
