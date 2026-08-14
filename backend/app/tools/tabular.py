"""Shared helpers for turning a SQL Executor result set into a pandas
DataFrame ready for analysis — used by both the Python Data Analyst
(`python_analyst.py`) and the Visualization Agent (`visualization.py`)."""
import pandas as pd


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """SQLAlchemy/psycopg return PostgreSQL NUMERIC columns as `Decimal`,
    which pandas stores as dtype `object` — invisible to
    `select_dtypes(include="number")`. Convert any object column that
    converts to numeric losslessly (every non-null value parses), so
    money/quantity columns are recognized as metrics."""
    for col in df.columns:
        if df[col].dtype != object:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() == df[col].notna().sum():
            df[col] = converted
    return df


def resolve_metric_column(df: pd.DataFrame, metric: str | None) -> str | None:
    """Picks the numeric column that best matches the Query Analyzer's
    `metric` name, falling back to the first numeric column. Returns None
    if the result set has no numeric column at all."""
    numeric_cols = list(df.select_dtypes(include="number").columns)
    if not numeric_cols:
        return None

    if metric:
        for col in df.columns:
            if metric.lower().replace(" ", "_") in col.lower() and col in numeric_cols:
                return col
    return numeric_cols[0]


def find_time_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    for col in df.columns:
        if any(hint in col.lower() for hint in ("date", "month", "period", "day", "year", "time")):
            return col
    return None
