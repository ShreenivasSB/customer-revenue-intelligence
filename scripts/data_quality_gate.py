"""
scripts/data_quality_gate.py

Automated data-quality gate for the ETL pipeline. Runs after
scripts/clean_data.py and before scripts/load_to_supabase.py — if this
script exits non-zero, the GitHub Actions workflow stops and the load
step never runs.

The checks are a direct port of the manual eyeballing done in
notebooks/01_data_quality_audit.ipynb and notebooks/02_data_cleaning.ipynb
(null rates, cancellation rates, duplicate rates, revenue sanity), turned
into pass/fail assertions with tolerance bands instead of one-off prints.

Usage:
    python scripts/data_quality_gate.py
Exit code 0 = PASS (all checks green), 1 = FAIL (at least one check red).
"""
import json
import sys

import pandas as pd

CLEAN_CSV_PATH = "data/processed/online_retail_clean.csv"
GUEST_CSV_PATH = "data/processed/guest_checkout.csv"
SUMMARY_JSON_PATH = "data/processed/cleaning_summary.json"

results = []


def check(name, condition, detail):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    return condition


def run_checks():
    with open(SUMMARY_JSON_PATH, encoding="utf-8") as f:
        summary = json.load(f)

    df = pd.read_csv(CLEAN_CSV_PATH, parse_dates=["InvoiceDate"], low_memory=False)
    guest = pd.read_csv(GUEST_CSV_PATH, parse_dates=["InvoiceDate"], low_memory=False)

    # ---- Volume sanity (wide bands — this is a static historical
    # dataset, so these mainly catch a broken/truncated download or a
    # cleaning regression, not day-to-day drift) ----
    check(
        "Raw row count in range",
        900_000 <= summary["raw_rows"] <= 1_200_000,
        f"raw_rows={summary['raw_rows']:,} (expected 900k-1.2M)",
    )
    null_pct = summary["guest_checkout_rows"] / summary["raw_rows"] * 100
    check(
        "Null Customer ID rate in range",
        15 <= null_pct <= 30,
        f"{null_pct:.2f}% of raw rows (expected 15-30%)",
    )
    dup_pct = summary["duplicates_removed"] / summary["raw_rows"] * 100
    check(
        "Duplicate rate in range",
        0 <= dup_pct <= 10,
        f"{dup_pct:.2f}% of raw rows (expected 0-10%)",
    )
    cancel_removed = summary["after_dedup"] - summary["after_cancellations_removed"]
    cancel_pct = cancel_removed / summary["raw_rows"] * 100
    check(
        "Cancellation rate in range",
        0.5 <= cancel_pct <= 5,
        f"{cancel_pct:.2f}% of raw rows (expected 0.5-5%)",
    )
    check(
        "Final clean row count above floor",
        summary["final_clean_rows"] >= 500_000,
        f"final_clean_rows={summary['final_clean_rows']:,} (expected >=500k)",
    )

    # ---- File/summary consistency (catches artifact corruption or a
    # script that silently disagrees with its own reported summary) ----
    check(
        "Clean CSV row count matches summary",
        len(df) == summary["final_clean_rows"],
        f"CSV has {len(df):,} rows, summary says {summary['final_clean_rows']:,}",
    )
    check(
        "Guest CSV row count matches summary",
        len(guest) == summary["guest_checkout_rows"],
        f"CSV has {len(guest):,} rows, summary says {summary['guest_checkout_rows']:,}",
    )

    # ---- Key-column completeness ----
    key_cols = ["Invoice", "Customer ID", "StockCode", "Quantity", "Price", "Revenue", "InvoiceDate"]
    nulls = df[key_cols].isnull().sum().sum()
    check(
        "No nulls in clean dataset's key columns",
        nulls == 0,
        f"{nulls} null values found across {key_cols}",
    )

    # ---- Value sanity ----
    check(
        "No non-positive price in clean dataset",
        (df["Price"] > 0).all(),
        f"min Price = {df['Price'].min()}",
    )
    check(
        "No non-positive quantity in clean dataset",
        (df["Quantity"] > 0).all(),
        f"min Quantity = {df['Quantity'].min()}",
    )
    check(
        "No revenue below the GBP 0.01 floor",
        (df["Revenue"] >= 0.01).all(),
        f"min Revenue = {df['Revenue'].min()}",
    )
    check(
        "No cancellation invoices leaked into clean dataset",
        not df["Invoice"].astype(str).str.startswith("C").any(),
        "checked Invoice column for 'C' prefix",
    )
    check(
        "Customer ID is fully populated and integer-typed",
        df["Customer ID"].notnull().all() and pd.api.types.is_integer_dtype(df["Customer ID"]),
        f"dtype={df['Customer ID'].dtype}, nulls={df['Customer ID'].isnull().sum()}",
    )

    # ---- Revenue totals within a wide sanity band (catches gross
    # unit/aggregation errors, e.g. revenue off by 10x or 100x) ----
    check(
        "Total clean revenue within sanity band",
        10_000_000 <= summary["final_clean_revenue"] <= 30_000_000,
        f"GBP {summary['final_clean_revenue']:,.2f} (expected GBP 10M-GBP 30M)",
    )
    check(
        "Guest checkout revenue within sanity band",
        1_000_000 <= summary["guest_checkout_revenue"] <= 10_000_000,
        f"GBP {summary['guest_checkout_revenue']:,.2f} (expected GBP 1M-GBP 10M)",
    )

    # ---- Guest stream sanity ----
    check(
        "Guest dataset has no populated Customer ID",
        guest["Customer ID"].isnull().all(),
        f"{guest['Customer ID'].notnull().sum()} non-null Customer IDs found in guest data",
    )
    check(
        "No non-positive price/quantity in guest dataset",
        (guest["Price"] > 0).all() and (guest["Quantity"] > 0).all(),
        f"min Price={guest['Price'].min()}, min Quantity={guest['Quantity'].min()}",
    )


def report():
    print("=" * 70)
    print("DATA QUALITY GATE")
    print("=" * 70)
    for name, status, detail in results:
        print(f"[{status}] {name}")
        print(f"       {detail}")
    print("=" * 70)

    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"{n_pass} passed, {n_fail} failed, {len(results)} total checks")
    print("=" * 70)

    if n_fail > 0:
        print("RESULT: FAIL — stopping pipeline before load.")
        return False
    print("RESULT: PASS — proceeding to load.")
    return True


def main():
    run_checks()
    passed = report()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
