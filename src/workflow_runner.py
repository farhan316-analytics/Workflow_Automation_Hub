from pathlib import Path
from datetime import datetime
import uuid

import psycopg2

from src.ingestion.file_ingestion import discover_files
from src.validation.data_validator import validate_file
from src.transformation.sales_transformer import process_daily_files
from src.database.db_loader import load_all_files
from src.analytics.kpi_engine import run_kpi_engine
from src.rules.business_rules import run_business_rules
from src.reporting.daily_report import run_report
from src.notifications.notification_engine import (
    run_notification_engine,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INCOMING_DIR = (
    PROJECT_ROOT
    / "data"
    / "incoming"
)


DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "workflow_automation",
    "user": "postgres",
}


def get_connection():

    import os

    password = os.getenv(
        "WORKFLOW_DB_PASSWORD"
    )

    if not password:
        raise ValueError(
            "WORKFLOW_DB_PASSWORD is not set."
        )

    return psycopg2.connect(
        host=os.getenv(
            "WORKFLOW_DB_HOST",
            DB_CONFIG["host"]
        ),
        port=os.getenv(
            "WORKFLOW_DB_PORT",
            DB_CONFIG["port"]
        ),
        database=os.getenv(
            "WORKFLOW_DB_NAME",
            DB_CONFIG["database"]
        ),
        user=os.getenv(
            "WORKFLOW_DB_USER",
            DB_CONFIG["user"]
        ),
        password=password,
    )

def create_parent_workflow_run(run_id, started_at):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analytics.workflow_runs (
                    run_id,
                    workflow_name,
                    started_at,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    run_id,
                    "Workflow Automation Hub",
                    started_at,
                    "RUNNING",
                )
            )

        connection.commit()

    finally:
        connection.close()

def update_workflow_run(
    run_id,
    status,
    completed_at=None,
    error_message=None,
):   
    run_id = str(run_id)

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE analytics.workflow_runs
                SET
                    status = %s,
                    completed_at = %s,
                    error_message = %s,
                    execution_seconds =
                        EXTRACT(
                            EPOCH FROM (
                                %s - started_at
                            )
                        )
                WHERE run_id = %s;
                """,
                (
                    status,
                    completed_at,
                    error_message,
                    completed_at,
                    run_id,
                )
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


def run_stage(
    stage_name,
    function,
):

    started = datetime.now()

    print()
    print("=" * 60)
    print(f"STAGE: {stage_name}")
    print("=" * 60)

    try:

        result = function()

        duration = (
            datetime.now() - started
        ).total_seconds()

        print(
            f"✅ {stage_name} completed "
            f"in {duration:.2f} seconds"
        )

        return result

    except Exception as error:

        duration = (
            datetime.now() - started
        ).total_seconds()

        print(
            f"❌ {stage_name} failed "
            f"after {duration:.2f} seconds"
        )

        print(
            f"Error: {error}"
        )

        raise


def validate_incoming_files():

    files = sorted(
    INCOMING_DIR.glob("sales_*.csv")
    )

    if not files:
        raise FileNotFoundError(
        "No production sales files found."
    )

    print(
        f"Files discovered: "
        f"{len(files):,}"
    )

    failed_files = []
    warning_files = []

    for file_path in files:

        result = validate_file(
            file_path
        )

        if result["status"] == "FAILED":

            failed_files.append(
                file_path.name
            )

        elif result["status"] == "WARNING":

            warning_files.append(
                file_path.name
            )

    print(
        f"Validation failures: "
        f"{len(failed_files):,}"
    )

    print(
        f"Validation warnings: "
        f"{len(warning_files):,}"
    )

    if failed_files:

        print()
        print(
            "Files rejected:"
        )

        for filename in failed_files:
            print(
                f"❌ {filename}"
            )

        raise ValueError(
            "Critical validation failures detected."
        )

    return {
        "files_discovered": len(files),
        "failed_files": failed_files,
        "warning_files": warning_files,
    }


def main():

    workflow_id = str(uuid.uuid4())
    started_at = datetime.now()

    create_parent_workflow_run(
        workflow_id,
        started_at
)

    started_at = datetime.now()

    print()
    print("=" * 70)
    print("WORKFLOW AUTOMATION HUB")
    print("END-TO-END WORKFLOW RUNNER")
    print("=" * 70)

    print()
    print(
        f"Workflow ID: {workflow_id}"
    )

    print(
        f"Started: {started_at}"
    )

    try:

        # ----------------------------------------------------
        # 1. VALIDATION
        # ----------------------------------------------------

        validation_result = run_stage(
            "DATA VALIDATION",
            validate_incoming_files,
        )

        # ----------------------------------------------------
        # 2. TRANSFORMATION
        # ----------------------------------------------------

        transformation_result = run_stage(
            "ETL TRANSFORMATION",
            process_daily_files,
        )

        # ----------------------------------------------------
        # 3. DATABASE LOAD
        # ----------------------------------------------------

        database_result = run_stage(
            "POSTGRESQL LOAD",
            load_all_files,
        )

        # ----------------------------------------------------
        # 4. KPI ENGINE
        # ----------------------------------------------------

        run_stage(
            "KPI CALCULATION",
            run_kpi_engine,
        )

        # ----------------------------------------------------
        # 5. BUSINESS RULES
        # ----------------------------------------------------

        run_stage(
            "BUSINESS RULE EVALUATION",
             lambda: run_business_rules(workflow_id),
        )

        # ----------------------------------------------------
        # 6. REPORT
        # ----------------------------------------------------

        run_stage(
            "REPORT GENERATION",
            run_report,
        )

        # ----------------------------------------------------
        # 7. NOTIFICATION
        # ----------------------------------------------------

        run_stage(
            "NOTIFICATION",
            run_notification_engine,
        )

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        completed_at = datetime.now()

        update_workflow_run(
            workflow_id,
            "SUCCESS",
            completed_at,
        )

        duration = (
            completed_at - started_at
        ).total_seconds()

        print()
        print("=" * 70)
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(
            f"Workflow ID: {workflow_id}"
        )

        print(
            f"Execution time: "
            f"{duration:.2f} seconds"
        )

        print(
            f"Files discovered: "
            f"{validation_result['files_discovered']:,}"
        )

        print(
            f"Validation warnings: "
            f"{len(validation_result['warning_files']):,}"
        )

        print(
            f"Database rows inserted: "
            f"{database_result:,}"
        )

        print(
            f"Transformation files: "
            f"{len(transformation_result):,}"
        )

        print()
        print(
            "FINAL STATUS: SUCCESS"
        )

        print("=" * 70)

    except Exception as error:

        completed_at = datetime.now()

        try:

            update_workflow_run(
                workflow_id,
                "FAILED",
                completed_at,
                str(error),
            )

        except Exception as audit_error:

            print(
                f"Audit logging failed: "
                f"{audit_error}"
            )

        print()
        print("=" * 70)
        print("❌ WORKFLOW FAILED")
        print("=" * 70)

        print(
            f"Workflow ID: {workflow_id}"
        )

        print(
            f"Error: {error}"
        )

        print(
            "FINAL STATUS: FAILED"
        )

        print("=" * 70)

        raise


if __name__ == "__main__":
    main()
    