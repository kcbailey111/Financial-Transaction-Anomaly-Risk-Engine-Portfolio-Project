import os
import sys
import time
import pandas as pd
from sqlalchemy import create_engine, inspect

# -------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# -------------------------------------------------------------------
# Keeping file paths centralized makes your code easy to update later.
RAW_DATA_PATH = os.path.join("data", "raw", "transactions.csv")
DB_PATH = os.path.join("data", "financial_warehouse.db")
TABLE_NAME = "raw_transactions"


def run_ingestion():
    print("=" * 60)
    print("🚀 STARTING FINANCIAL DATA INGESTION PIPELINE")
    print("=" * 60)

    start_time = time.time()

    # 1. VALIDATION: Check if raw dataset exists before proceeding
    if not os.path.exists(RAW_DATA_PATH):
        print(f"❌ ERROR: Raw CSV file not found at '{RAW_DATA_PATH}'.")
        print("   Please place your CSV inside 'data/raw/' and try again.")
        sys.exit(1)

    # 2. EXTRACT: Read raw CSV into memory using pandas
    print(f"📥 Reading raw data from: {RAW_DATA_PATH}...")
    try:
        df = pd.read_csv(RAW_DATA_PATH)
        row_count, col_count = df.shape
        print(f"✅ Successfully loaded raw dataset ({row_count:,} rows, {col_count} columns).")
    except Exception as e:
        print(f"❌ ERROR: Failed to read CSV file: {e}")
        sys.exit(1)

    # 3. SANITIZATION: Clean column names (strip whitespace, lowercase, replace spaces with _)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    print("\n📋 Sanitized Column Headers:")
    print(list(df.columns))

    # 4. LOAD: Initialize SQLite Database Connection via SQLAlchemy
    # 'sqlite:///' specifies the SQLite driver and relative file path
    db_url = f"sqlite:///{DB_PATH}"
    print(f"\n🔌 Connecting to SQLite database at: {DB_PATH}...")
    engine = create_engine(db_url, echo=False)

    # 5. WRITE: Load DataFrame into SQLite staging table
    print(f"💾 Writing records to staging table '{TABLE_NAME}'...")
    try:
        # if_exists='replace' drops the old staging table if it exists and rebuilds it.
        # chunksize=50000 ensures memory efficiency if handling large datasets.
        df.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=50000
        )
        print("✅ Data successfully written to database!")
    except Exception as e:
        print(f"❌ ERROR: Database write failed: {e}")
        sys.exit(1)

    # 6. VERIFICATION: Query database directly to confirm row counts match
    print("\n🔍 Verifying database write...")
    inspector = inspect(engine)
    if TABLE_NAME in inspector.get_table_names():
        with engine.connect() as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()
            db_row_count = result[0]
            
        print(f"📊 Verified Row Count in DB: {db_row_count:,} rows.")
        
        if db_row_count == row_count:
            print("✨ INTEGRITY CHECK PASSED: Data counts match perfectly!")
        else:
            print("⚠️ WARNING: Row count mismatch between CSV and DB table!")

    elapsed_time = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print(f"🎉 INGESTION PIPELINE COMPLETE IN {elapsed_time} SECONDS")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()