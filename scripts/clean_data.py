"""
scripts/clean_data.py

Downloads the raw UCI "Online Retail II" dataset (if not already present
locally) and produces two clean, analysis-ready datasets:
  - data/processed/online_retail_clean.csv  — identified customers only
  - data/processed/guest_checkout.csv       — null Customer ID rows
                                               (guest checkouts)
  - data/processed/cleaning_summary.json    — row counts at each cleaning
                                               step, consumed by
                                               scripts/data_quality_gate.py

This is a script refactor of the cleaning logic originally prototyped in
notebooks/01_data_quality_audit.ipynb and notebooks/02_data_cleaning.ipynb,
so it can run unattended in GitHub Actions. The cleaning rules and their
order are unchanged from the notebooks.

Usage:
    python scripts/clean_data.py [--force-download]
"""
import argparse
import io
import json
import os
import zipfile

import pandas as pd
import requests

UCI_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"

RAW_XLSX_PATH = "data/raw/online_retail_II.xlsx"
CLEAN_CSV_PATH = "data/processed/online_retail_clean.csv"
GUEST_CSV_PATH = "data/processed/guest_checkout.csv"
SUMMARY_JSON_PATH = "data/processed/cleaning_summary.json"


def download_raw(path=RAW_XLSX_PATH, url=UCI_URL, force=False):
    """Downloads and extracts the raw dataset if not already present locally."""
    if os.path.exists(path) and not force:
        print(f"Raw file already present at {path}, skipping download.")
        return path

    print(f"Downloading raw dataset from {url} ...")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        xlsx_name = next(n for n in zf.namelist() if n.lower().endswith(".xlsx"))
        with zf.open(xlsx_name) as src, open(path, "wb") as dst:
            dst.write(src.read())

    print(f"Downloaded and extracted to {path}")
    return path


def load_raw(path=RAW_XLSX_PATH):
    df_1 = pd.read_excel(path, sheet_name="Year 2009-2010", engine="openpyxl")
    df_2 = pd.read_excel(path, sheet_name="Year 2010-2011", engine="openpyxl")
    df = pd.concat([df_1, df_2], ignore_index=True)
    print(f"Raw dataset loaded: {len(df):,} rows, {df.shape[1]} columns")
    return df


def clean(df_raw):
    """
    Splits the raw dataset into two independently-derived streams:

    1. guest_df — null Customer ID rows (guest checkouts). Derived
       directly from df_raw with only Quantity>0 and Price>0 filters,
       matching the original null-customer analysis in notebook 02.
       Not deduplicated or cancellation-filtered beyond what those two
       filters naturally exclude (cancellations carry negative Quantity,
       so Quantity>0 already removes them) — this preserves the guest
       revenue totals already published in the README.

    2. df_clean — identified customers, cleaned via the full waterfall:
       dedup -> cancellations removed -> stock adjustments removed ->
       price>0 -> customer ID present -> revenue floor (>=£0.01).

    Returns (df_clean, guest_df, summary_dict).
    """
    summary = {"raw_rows": len(df_raw)}

    # ---- Guest checkout stream ----
    guest_df = df_raw[df_raw["Customer ID"].isnull()].copy()
    guest_df = guest_df[guest_df["Quantity"] > 0]
    guest_df = guest_df[guest_df["Price"] > 0]
    guest_df["Revenue"] = (guest_df["Quantity"] * guest_df["Price"]).round(2)
    summary["guest_checkout_rows"] = len(guest_df)
    summary["guest_checkout_revenue"] = round(float(guest_df["Revenue"].sum()), 2)

    # ---- Identified-customer stream ----
    df = df_raw.drop_duplicates()
    summary["after_dedup"] = len(df)
    summary["duplicates_removed"] = summary["raw_rows"] - summary["after_dedup"]

    df = df[~df["Invoice"].astype(str).str.startswith("C")]
    summary["after_cancellations_removed"] = len(df)

    df = df[~((df["Quantity"] < 0) & (~df["Invoice"].astype(str).str.startswith("C")))]
    summary["after_stock_adjustments_removed"] = len(df)

    df = df[df["Price"] > 0]
    summary["after_zero_neg_price_removed"] = len(df)

    df_clean = df[df["Customer ID"].notnull()].copy()
    summary["after_null_customer_removed"] = len(df_clean)

    df_clean["Customer ID"] = df_clean["Customer ID"].astype(int)
    df_clean["Revenue"] = (df_clean["Quantity"] * df_clean["Price"]).round(2)

    df_clean = df_clean[df_clean["Revenue"] >= 0.01]
    summary["final_clean_rows"] = len(df_clean)
    summary["final_clean_revenue"] = round(float(df_clean["Revenue"].sum()), 2)
    summary["unique_customers"] = int(df_clean["Customer ID"].nunique())

    return df_clean, guest_df, summary


def save(df_clean, guest_df, summary):
    os.makedirs(os.path.dirname(CLEAN_CSV_PATH), exist_ok=True)
    df_clean.to_csv(CLEAN_CSV_PATH, index=False)
    guest_df.to_csv(GUEST_CSV_PATH, index=False)
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Clean dataset saved: {CLEAN_CSV_PATH} ({len(df_clean):,} rows)")
    print(f"Guest checkout dataset saved: {GUEST_CSV_PATH} ({len(guest_df):,} rows)")
    print(f"Cleaning summary saved: {SUMMARY_JSON_PATH}")

    print("\n=== CLEANING SUMMARY ===")
    for k, v in summary.items():
        print(f"{k:35}{v:>15,}" if isinstance(v, (int, float)) else f"{k:35}{v}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download raw data even if a local copy already exists",
    )
    args = parser.parse_args()

    raw_path = download_raw(force=args.force_download)
    df_raw = load_raw(raw_path)
    df_clean, guest_df, summary = clean(df_raw)
    save(df_clean, guest_df, summary)


if __name__ == "__main__":
    main()
