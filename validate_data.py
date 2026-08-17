import pandas as pd
import sys

def validate(file_path):
    """Run all validation checks. Exit 1 on failure."""
    print("Validating: " + file_path)
    df = pd.read_csv(file_path)

    errors = []

    # Check 1: Required columns exist
    required_cols = ["customer_id", "order_id", "amount", "date", "segment"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append("Missing required columns: " + str(missing))
    else:
        print("PASS: All required columns present")

    # Check 2: Data types
    if "amount" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["amount"]):
            errors.append("Column 'amount' is not numeric")
        else:
            print("PASS: amount column is numeric")

    # Check 3: Minimum row count
    min_rows = 100
    if len(df) < min_rows:
        errors.append(
            "Row count " + str(len(df))
            + " below minimum " + str(min_rows)
        )
    else:
        print("PASS: Row count " + str(len(df)) + " meets minimum")

    # Check 4: No fully null columns
    null_cols = [c for c in df.columns if df[c].isnull().all()]
    if null_cols:
        errors.append("Fully null columns: " + str(null_cols))
    else:
        print("PASS: No fully null columns")

    # Report results
    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_data.py <file_path>")
        sys.exit(1)
    validate(sys.argv[1])
