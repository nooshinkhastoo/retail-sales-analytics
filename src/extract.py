from pathlib import Path
import pandas as pd


def extract_data(file_path):
    """
    Read raw CSV file and return pandas DataFrame.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(path)

    print("Data extracted successfully")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    return df


def profile_data(df):
    """
    Basic data profiling.
    """

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nData types:")
    print(df.dtypes)