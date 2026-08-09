from pathlib import Path

import os

from dotenv import load_dotenv


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# Project paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent
)

RAW_INPUT_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "retail_transactions_denormalized.csv"
)

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

REJECTED_DIR = (
    PROCESSED_DIR
    / "rejected_records"
)


# ============================================================
# Database
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/retail",
)
