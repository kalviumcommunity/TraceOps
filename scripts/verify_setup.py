import os
import sys

print("Python version:", sys.version)

try:
    import pandas as pd
    import numpy as np
    import matplotlib as mpl
    import seaborn as sns
    import sklearn
    import dotenv
    import openpyxl
    
    print("\n[SUCCESS] All packages successfully imported!")
    print(f"  pandas:       {pd.__version__}")
    print(f"  numpy:        {np.__version__}")
    print(f"  matplotlib:   {mpl.__version__}")
    print(f"  seaborn:      {sns.__version__}")
    print(f"  scikit-learn: {sklearn.__version__}")
    print(f"  dotenv:       Imported successfully")
    print(f"  openpyxl:     {openpyxl.__version__}")
except ImportError as e:
    print(f"\n[ERROR] Failed to import package: {e}")
    sys.exit(1)

# Check .env file if it exists
if os.path.exists(".env"):
    dotenv.load_dotenv()
    db_host = os.getenv("DB_HOST", "NOT SET")
    print(f"\nEnvironment Check:")
    print(f"  DB_HOST from .env: {db_host}")
else:
    print("\n[INFO] No .env file found (expected for clean clones; configure from .env.example).")
