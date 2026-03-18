# ============================================================
# Customer Revenue Intelligence & Retention Analytics System
# MySQL Ingestion Script
# Author: Shreenivas
# Description: Loads clean CSV data into MySQL star schema
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================
DB_USER     = "root"
DB_PASSWORD = "7736"
DB_HOST     = "localhost"
DB_PORT     = "3306"
DB_NAME     = "customer_revenue_intelligence"

CLEAN_CSV   = r"C:\Customer_Revenue_Intelligence\data\processed\online_retail_clean.csv"
RFM_CSV     = r"C:\Customer_Revenue_Intelligence\data\processed\rfm_segments.csv"

# ============================================================
# CONNECT TO MYSQL
# ============================================================
print("Connecting to MySQL...")
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("Connected successfully ✓")

# ============================================================
# LOAD DATA
# ============================================================
print("\nLoading clean dataset...")
df = pd.read_csv(CLEAN_CSV, parse_dates=['InvoiceDate'])
print(f"Loaded: {len(df):,} rows")

print("Loading RFM dataset...")
rfm = pd.read_csv(RFM_CSV)
print(f"Loaded: {len(rfm):,} customers")

# ============================================================
# POPULATE dim_customer
# ============================================================
print("\nPopulating dim_customer...")
dim_customer = df[['Customer ID', 'Country']].drop_duplicates(subset='Customer ID')
dim_customer.columns = ['customer_id', 'country']
dim_customer.to_sql('dim_customer', engine, if_exists='append', index=False)
print(f"dim_customer: {len(dim_customer):,} rows inserted ✓")

# ============================================================
# POPULATE dim_product
# ============================================================
print("\nPopulating dim_product...")
dim_product = df[['StockCode', 'Description']].drop_duplicates(subset='StockCode')
dim_product.columns = ['stock_code', 'description']
dim_product.to_sql('dim_product', engine, if_exists='append', index=False)
print(f"dim_product: {len(dim_product):,} rows inserted ✓")

# ============================================================
# POPULATE dim_date
# ============================================================
print("\nPopulating dim_date...")
df['date_only'] = df['InvoiceDate'].dt.date
dim_date = df[['date_only']].drop_duplicates()
dim_date.columns = ['date_id']
dim_date['year']        = pd.to_datetime(dim_date['date_id']).dt.year
dim_date['month']       = pd.to_datetime(dim_date['date_id']).dt.month
dim_date['day']         = pd.to_datetime(dim_date['date_id']).dt.day
dim_date['quarter']     = pd.to_datetime(dim_date['date_id']).dt.quarter
dim_date['month_name']  = pd.to_datetime(dim_date['date_id']).dt.strftime('%B')
dim_date['is_q4']       = dim_date['month'].isin([10, 11, 12]).astype(int)
dim_date.to_sql('dim_date', engine, if_exists='append', index=False)
print(f"dim_date: {len(dim_date):,} rows inserted ✓")

# ============================================================
# POPULATE fact_sales
# ============================================================
print("\nPopulating fact_sales...")
fact_sales = df[['Invoice', 'Customer ID', 'StockCode', 'date_only',
                  'Quantity', 'Price', 'Revenue']].copy()
fact_sales.columns = ['invoice', 'customer_id', 'stock_code', 'date_id',
                       'quantity', 'price', 'revenue']
fact_sales.to_sql('fact_sales', engine, if_exists='append',
                   index=False, chunksize=10000)
print(f"fact_sales: {len(fact_sales):,} rows inserted ✓")

# ============================================================
# POPULATE rfm_segments
# ============================================================
print("\nPopulating rfm_segments...")
rfm_clean = rfm.copy()
rfm_clean.columns = ['customer_id', 'recency', 'frequency', 'monetary',
                      'r_score', 'f_score', 'm_score', 'rfm_score',
                      'rfm_total', 'segment']
rfm_clean.to_sql('rfm_segments', engine, if_exists='append', index=False)
print(f"rfm_segments: {len(rfm_clean):,} rows inserted ✓")

# ============================================================
# VERIFY ROW COUNTS
# ============================================================
print("\n============================================================")
print("INGESTION COMPLETE — VERIFICATION")
print("============================================================")
with engine.connect() as conn:
    tables = ['dim_customer', 'dim_product', 'dim_date', 'fact_sales', 'rfm_segments']
    for table in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.fetchone()[0]
        print(f"{table:<20} {count:>10,} rows")
print("============================================================")