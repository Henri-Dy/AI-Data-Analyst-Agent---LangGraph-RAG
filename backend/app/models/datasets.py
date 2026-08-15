"""Schemas for the tabular datasets (CSV upload) management API."""
import datetime

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    table_name: str
    original_filename: str
    row_count: int
    columns: list[str]
    created_at: datetime.datetime


class DatasetUploadResponse(BaseModel):
    table_name: str
    row_count: int
    columns: list[str]
