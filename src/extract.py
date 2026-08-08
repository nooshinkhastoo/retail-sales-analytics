from pathlib import Path

import pandas as pd

from config import RAW_INPUT_PATH


def extract_data():
    """
    Read the raw retail transaction CSV file.

    Returns
    -------
    pandas.DataFrame
        Raw transaction data.
    """

    if not RAW_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Raw input file not found: {RAW_INPUT_PATH}"
        )

    print("Reading raw data...")
    print(f"Input file: {RAW_INPUT_PATH}")

    df = pd.read_csv(RAW_INPUT_PATH)

    print(
        f"Raw data loaded: {len(df):,} rows"
    )

    return df