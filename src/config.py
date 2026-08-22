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

REPORTS_DIR = (
    BASE_DIR
    / "reports"
)

CHARTS_DIR = (
    REPORTS_DIR
    / "charts"
)

ANALYSIS_QUERIES_PATH = (
    BASE_DIR
    / "sql"
    / "03_analysis_queries.sql"
)


# ============================================================
# Create required directories
# ============================================================

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REJECTED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CHARTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Database
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/retail",
)