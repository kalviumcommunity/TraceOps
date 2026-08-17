import os
import pandas as pd
import logging
import argparse
from datetime import datetime

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def ingest(path):
    """Stage 1: Load raw data."""
    logger.info("Ingesting data from: " + path)
    df = pd.read_csv(path)
    logger.info("Ingested " + str(len(df)) + " rows")
    return df

def clean(df):
    """Stage 2: Clean and validate."""
    logger.info("Cleaning data...")
    initial = len(df)
    df = df.dropna(subset=["customer_id", "amount"]).copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df[df["amount"] > 0]
    logger.info("Cleaned: " + str(initial) + " -> " + str(len(df)) + " rows")
    return df

def aggregate(df):
    """Stage 3: Compute aggregations."""
    logger.info("Aggregating...")
    agg = df.groupby("segment").agg(
        revenue=("amount", "sum"),
        orders=("order_id", "count")
    ).reset_index()
    logger.info("Aggregated " + str(len(agg)) + " segments")
    return agg

def output(df, agg, out_dir):
    """Stage 4: Write output files."""
    logger.info("Writing output to: " + out_dir)
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "cleaned.csv"), index=False)
    agg.to_csv(os.path.join(out_dir, "aggregated.csv"), index=False)
    logger.info("Output written to: " + out_dir)
    logger.info("Pipeline complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Data Pipeline Execution")
    parser.add_argument("--input", required=True, help="Path to raw input CSV file")
    parser.add_argument("--output", default="output", help="Directory path for output CSV files")
    args = parser.parse_args()

    raw = ingest(args.input)
    cleaned = clean(raw)
    agg = aggregate(cleaned)
    output(cleaned, agg, args.output)
