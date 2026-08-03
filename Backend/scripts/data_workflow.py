import os
import sys
import logging
import pandas as pd

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
INPUT_FILE = "data/raw/sample.csv"
OUTPUT_FILE = "output/processed.csv"
LOG_FILE = "output/workflow.log"

# ==========================================
# LOGGING SETUP
# ==========================================
# Ensure output log folder exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# MAIN WORKFLOW FUNCTIONS
# ==========================================

def ingest_data(filepath):
    """
    Load raw transaction or telemetry CSV data into a Pandas DataFrame.

    This function reads a CSV data source from the specified path, performs
    basic verification of file existence, and logs the load results.

    Args:
        filepath (str): The system path to the input CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing the loaded raw data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        pd.errors.EmptyDataError: If the input file is empty.
    """
    logging.info(f"Initiating ingestion from: {filepath}")
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Input file not found at: {filepath}")
            
        df = pd.read_csv(filepath)
        logging.info(f"Successfully ingested {len(df)} records from {filepath}")
        return df
    except FileNotFoundError as e:
        logging.error(f"Ingestion failed: {e}")
        raise
    except pd.errors.EmptyDataError as e:
        logging.error(f"Ingestion failed (empty file): {e}")
        raise
    except Exception as e:
        logging.error(f"Ingestion failed with unexpected error: {e}")
        raise

def process_data(df):
    """
    Apply cleaning and feature engineering transformations to the raw data.

    Cleans the raw DataFrame by executing the following rules:
    1. Removes exact duplicates to ensure row uniqueness.
    2. Fills missing values in numerical columns with their respective column medians
       (using median avoids skew from outliers).
    3. Engineers a new metric `items_per_minute` calculating operational speed.

    Args:
        df (pd.DataFrame): Ingested raw DataFrame containing:
            - order_id (int)
            - pick_duration_seconds (float/int)
            - item_count (float/int)

    Returns:
        pd.DataFrame: A cleaned and enriched DataFrame.
    """
    logging.info("Starting data processing and transformation...")
    rows_before = len(df)
    
    # 1. Deduplicate records
    df = df.drop_duplicates().copy()
    rows_after_dedup = len(df)
    duplicates_removed = rows_before - rows_after_dedup
    if duplicates_removed > 0:
        logging.info(f"Deduplication: Removed {duplicates_removed} duplicate rows.")
    
    # 2. Fill missing numerical fields with median
    # We use median instead of mean because skewed performance spikes shouldn't distort standard defaults
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logging.info(f"Data Cleaning: Filled {null_count} nulls in column '{col}' with median value ({median_val}).")

    # 3. Feature Engineering: Calculate picking throughput (items picked per minute)
    # Avoid division by zero by setting duration minimum threshold to 1 second
    df['pick_duration_seconds'] = df['pick_duration_seconds'].clip(lower=1)
    df['items_per_minute'] = (df['item_count'] / (df['pick_duration_seconds'] / 60.0)).round(2)
    logging.info("Feature Engineering: Computed 'items_per_minute' column.")

    logging.info(f"Processing completed successfully: {rows_before} raw rows -> {len(df)} processed rows.")
    return df

def output_results(df, output_path):
    """
    Save the transformed DataFrame to a CSV file and output console confirmation.

    Args:
        df (pd.DataFrame): Transformed and cleaned DataFrame.
        output_path (str): File destination path for the saved output.
    """
    logging.info(f"Initiating output write to: {output_path}")
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved processed results to {output_path}")
        
        # User-facing success messages (Task 4 requirement)
        print(f"✓ Data successfully processed")
        print(f"✓ Rows processed: {len(df)}")
        print(f"✓ Output saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write output results: {e}")
        raise

# ==========================================
# PIPELINE EXECUTION ORCHESTRATION
# ==========================================
if __name__ == "__main__":
    # Force stdout/stderr to use UTF-8 on Windows to prevent charmap UnicodeEncodeError
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    try:
        print("Starting TraceOps Data Ingestion & Validation Workflow...")
        logging.info("=== WORKFLOW PIPELINE INITIATED ===")
        
        # Step 1: Ingest
        raw_data = ingest_data(INPUT_FILE)
        
        # Step 2: Process
        processed_data = process_data(raw_data)
        
        # Step 3: Output
        output_results(processed_data, OUTPUT_FILE)
        
        print("✓ Workflow completed successfully")
        logging.info("=== WORKFLOW PIPELINE COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        logging.error(f"=== WORKFLOW PIPELINE FAILED === Error: {str(e)}")
        print(f"\n[FATAL ERROR] Workflow execution failed: {str(e)}")
        sys.exit(1)
