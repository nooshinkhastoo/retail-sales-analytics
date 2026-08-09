from config import DATABASE_URL
from extract import extract_data
from transform import transform_data
from load import get_connection, load_data
from quality import run_quality_checks
from reports import run_all_reports


def main():
    """
    Run the complete Retail Analytics pipeline.
    """

    print("=" * 60)
    print("Retail Analytics Pipeline Started")
    print("=" * 60)

    conn = None

    try:
        # ====================================================
        # 1. Extract
        # ====================================================

        print()
        print("[1/5] Extracting raw data...")

        df, _ = extract_data()

        # ====================================================
        # 2. Transform
        # ====================================================

        print()
        print("[2/5] Transforming data...")

        tables = transform_data(df)

        # Raw DataFrame is no longer needed after transformation.
        del df

        # ====================================================
        # 3. Load
        # ====================================================

        print()
        print("[3/5] Loading data into PostgreSQL...")

        conn = get_connection(
            {
                "dsn": DATABASE_URL
            }
        )

        load_data(
            conn,
            tables,
        )

        # ====================================================
        # 4. Quality checks
        # ====================================================

        print()
        print("[4/5] Running quality checks...")

        quality_results = run_quality_checks(conn)

        # ====================================================
        # 5. Analytical reports
        # ====================================================

        print()
        print("[5/5] Running analytical reports...")

        report_results = run_all_reports(conn)

        # ====================================================
        # Pipeline completed
        # ====================================================

        print()
        print("=" * 60)
        print("Retail Analytics Pipeline Completed Successfully")
        print("=" * 60)

        return {
            "quality": quality_results,
            "reports": report_results,
        }

    except Exception as e:

        print()
        print("=" * 60)
        print("Retail Analytics Pipeline FAILED")
        print("=" * 60)

        print(f"Error: {e}")

        raise

    finally:

        if conn is not None:
            conn.close()

            print()
            print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
