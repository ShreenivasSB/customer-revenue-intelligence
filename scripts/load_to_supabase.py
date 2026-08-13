"""
scripts/load_to_supabase.py

Loads the cleaned CSVs (produced by scripts/clean_data.py, and validated
by scripts/data_quality_gate.py) into the Supabase Postgres warehouse,
then computes RFM segments directly in SQL via sql/compute_rfm.sql
(NTILE(5) quintiles — not pandas/pd.qcut).

Every run truncates and reloads all tables, so it is safe to re-run on
a schedule even though the underlying dataset does not change day to
day — this mirrors how a real incremental pipeline would be structured,
just without the incremental part (there is nothing to increment against
a static historical dataset).

Reads the connection string from the DATABASE_URL environment variable.
Supabase gives you this on the project's Database Settings page (use the
connection pooler string for serverless/CI contexts). See .env.example.

Usage:
    python scripts/load_to_supabase.py
"""
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

CLEAN_CSV_PATH = "data/processed/online_retail_clean.csv"
GUEST_CSV_PATH = "data/processed/guest_checkout.csv"
SCHEMA_DDL_PATH = "sql/schema_ddl_postgres.sql"
RFM_SQL_PATH = "sql/compute_rfm.sql"


def get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set.", file=sys.stderr)
        print("Set it to your Supabase Postgres connection string (see .env.example).", file=sys.stderr)
        sys.exit(1)
    if db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url)


def _strip_sql_comments(sql_text):
    lines = [line for line in sql_text.splitlines() if not line.strip().startswith("--")]
    return "\n".join(lines)


def _split_statements(sql_text):
    cleaned = _strip_sql_comments(sql_text)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def run_sql_file(engine, path, label):
    print(f"{label}...")
    with open(path, encoding="utf-8") as f:
        sql_text = f.read()
    with engine.begin() as conn:
        for stmt in _split_statements(sql_text):
            conn.execute(text(stmt))
    print(f"{label} — done.")


def truncate_all(engine):
    print("Truncating existing data (idempotent reload)...")
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE TABLE fact_sales, fact_guest_checkout, rfm_segments, "
            "dim_customer, dim_product, dim_date RESTART IDENTITY CASCADE"
        ))
    print("Truncated.")


def load_dims_and_facts(engine):
    print("Loading clean dataset...")
    df = pd.read_csv(CLEAN_CSV_PATH, parse_dates=["InvoiceDate"], low_memory=False)
    print(f"Loaded: {len(df):,} rows")

    print("Loading guest checkout dataset...")
    guest = pd.read_csv(GUEST_CSV_PATH, parse_dates=["InvoiceDate"], low_memory=False)
    print(f"Loaded: {len(guest):,} rows")

    df["date_only"] = df["InvoiceDate"].dt.date
    guest["date_only"] = guest["InvoiceDate"].dt.date

    # ---- dim_customer ----
    dim_customer = df[["Customer ID", "Country"]].drop_duplicates(subset="Customer ID")
    dim_customer.columns = ["customer_id", "country"]
    dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
    print(f"dim_customer: {len(dim_customer):,} rows inserted")

    # ---- dim_product (union of both streams' stock codes) ----
    prod_cols = ["StockCode", "Description"]
    dim_product = pd.concat([df[prod_cols], guest[prod_cols]], ignore_index=True)
    dim_product = dim_product.drop_duplicates(subset="StockCode")
    dim_product.columns = ["stock_code", "description"]
    dim_product.to_sql("dim_product", engine, if_exists="append", index=False)
    print(f"dim_product: {len(dim_product):,} rows inserted")

    # ---- dim_date (union of both streams' dates) ----
    all_dates = pd.concat([df[["date_only"]], guest[["date_only"]]], ignore_index=True)
    dim_date = all_dates.drop_duplicates().copy()
    dim_date.columns = ["date_id"]
    dim_date["year"] = pd.to_datetime(dim_date["date_id"]).dt.year
    dim_date["month"] = pd.to_datetime(dim_date["date_id"]).dt.month
    dim_date["day"] = pd.to_datetime(dim_date["date_id"]).dt.day
    dim_date["quarter"] = pd.to_datetime(dim_date["date_id"]).dt.quarter
    dim_date["month_name"] = pd.to_datetime(dim_date["date_id"]).dt.strftime("%B")
    dim_date["is_q4"] = dim_date["month"].isin([10, 11, 12])
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"dim_date: {len(dim_date):,} rows inserted")

    # ---- fact_sales ----
    fact_sales = df[["Invoice", "Customer ID", "StockCode", "date_only",
                      "Quantity", "Price", "Revenue"]].copy()
    fact_sales.columns = ["invoice", "customer_id", "stock_code", "date_id",
                           "quantity", "price", "revenue"]
    fact_sales.to_sql("fact_sales", engine, if_exists="append", index=False, chunksize=10000)
    print(f"fact_sales: {len(fact_sales):,} rows inserted")

    # ---- fact_guest_checkout ----
    fact_guest = guest[["Invoice", "StockCode", "date_only", "Country",
                         "Quantity", "Price", "Revenue"]].copy()
    fact_guest.columns = ["invoice", "stock_code", "date_id", "country",
                           "quantity", "price", "revenue"]
    fact_guest.to_sql("fact_guest_checkout", engine, if_exists="append", index=False, chunksize=10000)
    print(f"fact_guest_checkout: {len(fact_guest):,} rows inserted")


def verify(engine):
    print("\n" + "=" * 60)
    print("LOAD COMPLETE — VERIFICATION")
    print("=" * 60)
    tables = ["dim_customer", "dim_product", "dim_date", "fact_sales",
              "fact_guest_checkout", "rfm_segments"]
    with engine.connect() as conn:
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"{table:<22} {count:>10,} rows")
    print("=" * 60)


def main():
    engine = get_engine()
    run_sql_file(engine, SCHEMA_DDL_PATH, "Ensuring schema exists")
    truncate_all(engine)
    load_dims_and_facts(engine)
    run_sql_file(engine, RFM_SQL_PATH, "Computing RFM segments in SQL (NTILE quintiles)")
    verify(engine)


if __name__ == "__main__":
    main()
