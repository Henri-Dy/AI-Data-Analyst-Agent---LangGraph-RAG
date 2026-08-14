"""Loads the generated demo dataset CSVs (data/raw/*.csv) into PostgreSQL.

Run with: python scripts/seed_database.py
Requires data/raw/*.csv to already exist (see data/generate_dataset.py) and
the database schema to already be migrated (alembic upgrade head).
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import engine  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Load order matters: parents before children (foreign key dependencies).
TABLES_IN_ORDER = ["regions", "employees", "customers", "products", "orders", "order_items"]

DATE_COLUMNS = {
    "employees": ["hire_date"],
    "customers": ["signup_date"],
    "products": ["launch_date"],
    "orders": ["order_date"],
}


def truncate_all() -> None:
    with engine.begin() as conn:
        tables = ", ".join(reversed(TABLES_IN_ORDER))
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


def load_table(name: str) -> int:
    csv_path = DATA_DIR / f"{name}.csv"
    # "NA" is a valid region code (North America), not a missing value — only
    # truly empty fields (e.g. missing customer phone numbers) should become NULL.
    df = pd.read_csv(
        csv_path, keep_default_na=False, na_values=[""], parse_dates=DATE_COLUMNS.get(name, [])
    )
    df.to_sql(name, engine, if_exists="append", index=False, method="multi", chunksize=5000)
    return len(df)


def main() -> None:
    print("Truncating existing data...")
    truncate_all()

    for table in TABLES_IN_ORDER:
        count = load_table(table)
        print(f"{table:<15} {count:>8,} rows loaded")

    print("\nDone.")


if __name__ == "__main__":
    main()
