"""Generates a realistic demo dataset for the AI Data Analyst Agent.

Produces CSV files under data/raw/: regions, employees, customers, products,
orders, order_items. The data intentionally encodes:

- multi-year revenue growth with weekday/monthly seasonality
- a pronounced revenue decline in the final month (July 2025), driven by a
  combination of one underperforming region, a shrinking enterprise segment,
  and a handful of declining products — so root-cause questions have a real
  answer grounded in the data
- a few one-off anomalies (flash-sale spikes, an outage day)
- realistic missing values (some customers have no phone on file)

Run with: python data/generate_dataset.py
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
OUT_DIR = Path(__file__).parent / "raw"

START_DATE = dt.date(2023, 1, 1)
END_DATE = dt.date(2025, 7, 31)
DECLINE_YEAR, DECLINE_MONTH = 2025, 7

N_CUSTOMERS = 1500
N_EMPLOYEES = 60
N_PRODUCTS = 130
N_ORDERS = 56000

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Amara", "Wei", "Sofia", "Noah", "Liam",
    "Olivia", "Emma", "Ava", "Yuki", "Hiro", "Fatima", "Ahmed", "Priya", "Raj",
    "Carlos", "Maria", "Lucas", "Isabella", "Mateus", "Camila",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Kim", "Chen", "Nakamura",
    "Khan", "Silva", "Santos", "Oliveira", "Dubois", "Muller", "Rossi", "Kowalski",
]

REGIONS = [
    {"id": 1, "name": "North America", "country": "United States", "code": "NA"},
    {"id": 2, "name": "Europe", "country": "Germany", "code": "EU"},
    {"id": 3, "name": "APAC", "country": "Singapore", "code": "AP"},
    {"id": 4, "name": "Latin America", "country": "Brazil", "code": "LATAM"},
    {"id": 5, "name": "Middle East & Africa", "country": "United Arab Emirates", "code": "MEA"},
    {"id": 6, "name": "Oceania", "country": "Australia", "code": "OC"},
]
REGION_WEIGHTS_NORMAL = {1: 0.34, 2: 0.26, 3: 0.20, 4: 0.11, 5: 0.05, 6: 0.04}
# APAC is the underperforming region behind the July revenue decline.
REGION_WEIGHTS_DECLINE = {1: 0.36, 2: 0.28, 3: 0.09, 4: 0.13, 5: 0.07, 6: 0.07}

SEGMENTS = ["consumer", "smb", "enterprise"]
SEGMENT_WEIGHTS_NORMAL = {"consumer": 0.55, "smb": 0.30, "enterprise": 0.15}
# Enterprise demand softens in the decline month too.
SEGMENT_WEIGHTS_DECLINE = {"consumer": 0.62, "smb": 0.30, "enterprise": 0.08}

CATEGORIES = {
    "Electronics": {"subcats": ["Laptops", "Phones", "Audio", "Accessories"], "price": (50, 2000)},
    "Software": {"subcats": ["Productivity", "Security", "Design", "Developer Tools"], "price": (20, 500)},
    "Office Supplies": {"subcats": ["Paper", "Writing", "Storage", "Desk Accessories"], "price": (2, 100)},
    "Furniture": {"subcats": ["Desks", "Chairs", "Storage", "Lighting"], "price": (50, 1500)},
    "Apparel": {"subcats": ["Outerwear", "Footwear", "Accessories", "Workwear"], "price": (15, 300)},
    "Home & Garden": {"subcats": ["Kitchen", "Decor", "Outdoor", "Tools"], "price": (10, 400)},
}
MODEL_WORDS = ["Pro", "Air", "Max", "Lite", "Plus", "Elite", "Core", "Edge", "Prime", "Flex"]

ORDER_STATUS_WEIGHTS = {"completed": 0.90, "cancelled": 0.05, "refunded": 0.03, "pending": 0.02}
ORDER_CHANNEL_WEIGHTS = {"online": 0.60, "retail": 0.30, "phone": 0.10}


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    n_days = (end - start).days + 1
    return [start + dt.timedelta(days=i) for i in range(n_days)]


def generate_regions() -> pd.DataFrame:
    return pd.DataFrame(REGIONS)


def generate_employees(regions_df: pd.DataFrame) -> pd.DataFrame:
    per_region = N_EMPLOYEES // len(regions_df)
    rows = []
    emp_id = 1
    roles = ["Sales Rep", "Account Manager", "Sales Director"]
    role_weights = [0.7, 0.25, 0.05]
    for region_id in regions_df["id"]:
        for _ in range(per_region):
            hire_date = START_DATE - dt.timedelta(days=int(RNG.integers(0, 365 * 5)))
            rows.append(
                {
                    "id": emp_id,
                    "first_name": RNG.choice(FIRST_NAMES),
                    "last_name": RNG.choice(LAST_NAMES),
                    "role": RNG.choice(roles, p=role_weights),
                    "hire_date": hire_date,
                    "region_id": region_id,
                }
            )
            emp_id += 1
    return pd.DataFrame(rows)


def generate_customers(regions_df: pd.DataFrame) -> pd.DataFrame:
    region_ids = RNG.choice(
        regions_df["id"], size=N_CUSTOMERS, p=list(REGION_WEIGHTS_NORMAL.values())
    )
    segments = RNG.choice(SEGMENTS, size=N_CUSTOMERS, p=list(SEGMENT_WEIGHTS_NORMAL.values()))
    signup_days_ago = RNG.integers(0, (END_DATE - START_DATE).days, size=N_CUSTOMERS)
    has_phone = RNG.random(N_CUSTOMERS) > 0.08  # ~8% missing phone, realistic dirty data

    rows = []
    for i in range(N_CUSTOMERS):
        first = RNG.choice(FIRST_NAMES)
        last = RNG.choice(LAST_NAMES)
        rows.append(
            {
                "id": i + 1,
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}{i + 1}@example.com",
                "phone": f"+1-555-{RNG.integers(1000, 9999)}" if has_phone[i] else None,
                "segment": segments[i],
                "signup_date": START_DATE + dt.timedelta(days=int(signup_days_ago[i])),
                "region_id": int(region_ids[i]),
            }
        )
    return pd.DataFrame(rows)


def generate_products() -> pd.DataFrame:
    rows = []
    pid = 1
    categories = list(CATEGORIES.items())
    for i in range(N_PRODUCTS):
        category, spec = categories[i % len(categories)]
        subcat = RNG.choice(spec["subcats"])
        low, high = spec["price"]
        unit_price = round(float(RNG.uniform(low, high)), 2)
        cost = round(unit_price * float(RNG.uniform(0.4, 0.7)), 2)
        launch_days_ago = int(RNG.integers(0, 365 * 5))
        is_active = RNG.random() > 0.10  # ~10% discontinued
        rows.append(
            {
                "id": pid,
                "sku": f"SKU-{pid:05d}",
                "name": f"{subcat} {RNG.choice(MODEL_WORDS)} {pid}",
                "category": category,
                "subcategory": subcat,
                "unit_price": unit_price,
                "cost": cost,
                "launch_date": START_DATE - dt.timedelta(days=launch_days_ago),
                "is_active": bool(is_active),
                # Skewed popularity so a handful of products dominate revenue.
                "_popularity": float(RNG.exponential(scale=1.0)),
            }
        )
        pid += 1
    return pd.DataFrame(rows)


def compute_daily_weights(days: list[dt.date]) -> np.ndarray:
    weights = np.ones(len(days))
    for i, day in enumerate(days):
        days_since_start = (day - START_DATE).days
        growth = 1 + 0.18 * (days_since_start / 365)  # ~18%/year growth trend
        weekday_factor = 1.1 if day.weekday() < 5 else 0.65
        month_factor = {
            1: 0.85, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.0, 6: 0.95,
            7: 0.85, 8: 0.9, 9: 1.0, 10: 1.05, 11: 1.3, 12: 1.5,
        }[day.month]
        decline_factor = 0.72 if (day.year == DECLINE_YEAR and day.month == DECLINE_MONTH) else 1.0
        weights[i] = growth * weekday_factor * month_factor * decline_factor

    # A few one-off anomalies: flash-sale spikes and one outage day.
    spike_idx = RNG.choice(len(days), size=3, replace=False)
    weights[spike_idx] *= 4.5
    outage_idx = RNG.choice([i for i in range(len(days)) if i not in spike_idx])
    weights[outage_idx] *= 0.05

    return weights / weights.sum()


def generate_orders_and_items(
    customers_df: pd.DataFrame, employees_df: pd.DataFrame, products_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    days = date_range(START_DATE, END_DATE)
    day_probs = compute_daily_weights(days)
    order_dates = RNG.choice(np.array(days, dtype=object), size=N_ORDERS, p=day_probs)

    is_decline_month = np.array(
        [d.year == DECLINE_YEAR and d.month == DECLINE_MONTH for d in order_dates]
    )

    region_ids = np.empty(N_ORDERS, dtype=int)
    segments = np.empty(N_ORDERS, dtype=object)
    for mask, region_w, segment_w in (
        (is_decline_month, REGION_WEIGHTS_DECLINE, SEGMENT_WEIGHTS_DECLINE),
        (~is_decline_month, REGION_WEIGHTS_NORMAL, SEGMENT_WEIGHTS_NORMAL),
    ):
        n = int(mask.sum())
        if n == 0:
            continue
        region_ids[mask] = RNG.choice(list(region_w.keys()), size=n, p=list(region_w.values()))
        segments[mask] = RNG.choice(list(segment_w.keys()), size=n, p=list(segment_w.values()))

    customers_by_bucket: dict[tuple[int, str], np.ndarray] = {
        (rid, seg): grp["id"].to_numpy()
        for (rid, seg), grp in customers_df.groupby(["region_id", "segment"])
    }
    customers_by_region: dict[int, np.ndarray] = {
        rid: grp["id"].to_numpy() for rid, grp in customers_df.groupby("region_id")
    }
    employees_by_region: dict[int, np.ndarray] = {
        rid: grp["id"].to_numpy() for rid, grp in employees_df.groupby("region_id")
    }

    customer_ids = np.empty(N_ORDERS, dtype=int)
    employee_ids = np.empty(N_ORDERS, dtype=int)
    for i in range(N_ORDERS):
        rid, seg = int(region_ids[i]), segments[i]
        pool = customers_by_bucket.get((rid, seg))
        if pool is None or len(pool) == 0:
            pool = customers_by_region[rid]
        customer_ids[i] = RNG.choice(pool)
        employee_ids[i] = RNG.choice(employees_by_region[rid])

    is_recent = np.array([(END_DATE - d).days <= 3 for d in order_dates])
    statuses = np.empty(N_ORDERS, dtype=object)
    non_pending = {k: v for k, v in ORDER_STATUS_WEIGHTS.items() if k != "pending"}
    norm = sum(non_pending.values())
    non_pending_w = [v / norm for v in non_pending.values()]
    statuses[~is_recent] = RNG.choice(list(non_pending.keys()), size=int((~is_recent).sum()), p=non_pending_w)
    statuses[is_recent] = RNG.choice(
        list(ORDER_STATUS_WEIGHTS.keys()), size=int(is_recent.sum()), p=list(ORDER_STATUS_WEIGHTS.values())
    )
    channels = RNG.choice(
        list(ORDER_CHANNEL_WEIGHTS.keys()), size=N_ORDERS, p=list(ORDER_CHANNEL_WEIGHTS.values())
    )

    orders_df = pd.DataFrame(
        {
            "id": np.arange(1, N_ORDERS + 1),
            "order_date": order_dates,
            "status": statuses,
            "channel": channels,
            "customer_id": customer_ids,
            "employee_id": employee_ids,
            "region_id": region_ids,
        }
    )

    order_items_df = generate_order_items(orders_df, products_df)
    return orders_df, order_items_df


def generate_order_items(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    n_orders = len(orders_df)
    items_per_order = RNG.choice([1, 2, 3, 4, 5], size=n_orders, p=[0.35, 0.30, 0.20, 0.10, 0.05])
    order_id_expanded = np.repeat(orders_df["id"].to_numpy(), items_per_order)
    order_date_expanded = np.repeat(orders_df["order_date"].to_numpy(), items_per_order)
    n_items = len(order_id_expanded)

    # A handful of active products lose demand over the last 6 months, with a
    # sharper drop in the decline month itself — a concrete, queryable cause
    # behind "which products have declining sales?".
    declining_product_ids = set(
        products_df[products_df["is_active"]].sample(n=6, random_state=7)["id"]
    )

    order_dates_pd = pd.to_datetime(order_date_expanded)
    is_july_decline = (order_dates_pd.year == DECLINE_YEAR) & (order_dates_pd.month == DECLINE_MONTH)
    is_decline_window = (order_dates_pd >= pd.Timestamp(2025, 2, 1)) & (order_dates_pd <= pd.Timestamp(2025, 6, 30))

    base_weights = np.where(
        products_df["is_active"], products_df["_popularity"], products_df["_popularity"] * 0.05
    )

    is_july_decline = np.asarray(is_july_decline)
    is_decline_window = np.asarray(is_decline_window)

    product_ids = np.empty(n_items, dtype=int)
    for mask, multiplier_map in (
        (is_july_decline, 0.25),
        (is_decline_window & ~is_july_decline, 0.6),
        (~is_decline_window & ~is_july_decline, 1.0),
    ):
        n = int(mask.sum())
        if n == 0:
            continue
        weights = base_weights.copy()
        decline_mask = products_df["id"].isin(declining_product_ids).to_numpy()
        weights = np.where(decline_mask, weights * multiplier_map, weights)
        probs = weights / weights.sum()
        product_ids[mask] = RNG.choice(products_df["id"].to_numpy(), size=n, p=probs)

    price_lookup = products_df.set_index("id")["unit_price"]
    base_prices = price_lookup.loc[product_ids].to_numpy()
    noise = RNG.uniform(0.95, 1.05, size=n_items)
    unit_prices = np.round(base_prices * noise, 2)

    has_discount = RNG.random(n_items) < 0.20
    discount_pct = np.where(has_discount, np.round(RNG.uniform(0.05, 0.30, size=n_items), 3), 0.0)

    quantities = RNG.choice([1, 2, 3, 4, 5], size=n_items, p=[0.45, 0.25, 0.15, 0.10, 0.05])

    return pd.DataFrame(
        {
            "id": np.arange(1, n_items + 1),
            "order_id": order_id_expanded,
            "product_id": product_ids,
            "quantity": quantities,
            "unit_price": unit_prices,
            "discount_pct": discount_pct,
        }
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    regions_df = generate_regions()
    employees_df = generate_employees(regions_df)
    customers_df = generate_customers(regions_df)
    products_df = generate_products()
    orders_df, order_items_df = generate_orders_and_items(customers_df, employees_df, products_df)

    products_out = products_df.drop(columns=["_popularity"])

    datasets = {
        "regions": regions_df,
        "employees": employees_df,
        "customers": customers_df,
        "products": products_out,
        "orders": orders_df,
        "order_items": order_items_df,
    }
    for name, df in datasets.items():
        path = OUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"{name:<15} {len(df):>8,} rows -> {path}")

    revenue = order_items_df["unit_price"] * order_items_df["quantity"] * (1 - order_items_df["discount_pct"])
    print(f"\nTotal simulated gross revenue: ${revenue.sum():,.2f}")


if __name__ == "__main__":
    main()
