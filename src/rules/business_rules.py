from pathlib import Path
import os
import uuid
from datetime import datetime

import psycopg2


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_CONFIG = {
    "host": os.getenv(
        "WORKFLOW_DB_HOST",
        "localhost"
    ),
    "port": os.getenv(
        "WORKFLOW_DB_PORT",
        "5432"
    ),
    "database": os.getenv(
        "WORKFLOW_DB_NAME",
        "workflow_automation"
    ),
    "user": os.getenv(
        "WORKFLOW_DB_USER",
        "postgres"
    ),
    "password": os.getenv(
        "WORKFLOW_DB_PASSWORD"
    ),
}


# ============================================================
# BUSINESS RULE THRESHOLDS
# ============================================================

REVENUE_DECLINE_THRESHOLD = -20.0
ORDER_DECLINE_THRESHOLD = -15.0
AOV_DECLINE_THRESHOLD = -15.0

REVENUE_SPIKE_THRESHOLD = 30.0


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    if not DB_CONFIG["password"]:
        raise ValueError(
            "WORKFLOW_DB_PASSWORD environment variable "
            "is not set."
        )

    return psycopg2.connect(
        **DB_CONFIG
    )


# ============================================================
# CREATE WORKFLOW RUN
# ============================================================

def create_workflow_run(run_id):

    started_at = datetime.now()

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
                    "Daily Sales Business Rules",
                    started_at,
                    "RUNNING",
                )
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    return run_id, started_at


# ============================================================
# LOAD KPI DATA
# ============================================================

def load_kpis():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    kpi_date,
                    revenue,
                    orders,
                    units_sold,
                    average_order_value,
                    average_units_per_order,
                    unique_customers,
                    revenue_growth_pct,
                    order_growth_pct
                FROM analytics.daily_kpis
                ORDER BY kpi_date;
                """
            )

            rows = cursor.fetchall()

    finally:

        connection.close()

    return rows


# ============================================================
# CLEAR EXISTING ALERTS FOR RUN
# ============================================================

def clear_existing_alerts(run_id):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM analytics.business_alerts
                WHERE run_id = %s;
                """,
                (run_id,)
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ============================================================
# CREATE ALERT
# ============================================================

def create_alert(
    run_id,
    alert_date,
    alert_type,
    severity,
    metric_name,
    actual_value,
    threshold_value,
    change_pct,
    message,
):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO analytics.business_alerts (
                    run_id,
                    alert_date,
                    alert_type,
                    severity,
                    metric_name,
                    actual_value,
                    threshold_value,
                    change_pct,
                    message,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'OPEN'
                );
                """,
                (
                    run_id,
                    alert_date,
                    alert_type,
                    severity,
                    metric_name,
                    actual_value,
                    threshold_value,
                    change_pct,
                    message,
                )
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ============================================================
# APPLY BUSINESS RULES
# ============================================================

def evaluate_business_rules(
    run_id,
    kpi_rows
):

    alerts_generated = 0

    for row in kpi_rows:

        (
            kpi_date,
            revenue,
            orders,
            units_sold,
            average_order_value,
            average_units_per_order,
            unique_customers,
            revenue_growth_pct,
            order_growth_pct,
        ) = row

        # ----------------------------------------------------
        # RULE 1 — REVENUE DECLINE
        # ----------------------------------------------------

        if (
            revenue_growth_pct
            <= REVENUE_DECLINE_THRESHOLD
        ):

            create_alert(
                run_id=run_id,
                alert_date=kpi_date,
                alert_type="REVENUE_DECLINE",
                severity="HIGH",
                metric_name="revenue",
                actual_value=float(revenue),
                threshold_value=(
                    REVENUE_DECLINE_THRESHOLD
                ),
                change_pct=float(
                    revenue_growth_pct
                ),
                message=(
                    f"Revenue declined by "
                    f"{abs(revenue_growth_pct):.2f}% "
                    f"on {kpi_date}, exceeding "
                    f"the {abs(REVENUE_DECLINE_THRESHOLD):.0f}% "
                    "decline threshold."
                ),
            )

            alerts_generated += 1

        # ----------------------------------------------------
        # RULE 2 — ORDER DECLINE
        # ----------------------------------------------------

        if (
            order_growth_pct
            <= ORDER_DECLINE_THRESHOLD
        ):

            create_alert(
                run_id=run_id,
                alert_date=kpi_date,
                alert_type="ORDER_DECLINE",
                severity="MEDIUM",
                metric_name="orders",
                actual_value=float(orders),
                threshold_value=(
                    ORDER_DECLINE_THRESHOLD
                ),
                change_pct=float(
                    order_growth_pct
                ),
                message=(
                    f"Orders declined by "
                    f"{abs(order_growth_pct):.2f}% "
                    f"on {kpi_date}, exceeding "
                    f"the {abs(ORDER_DECLINE_THRESHOLD):.0f}% "
                    "decline threshold."
                ),
            )

            alerts_generated += 1

        # ----------------------------------------------------
        # RULE 3 — REVENUE SPIKE
        # ----------------------------------------------------

        if (
            revenue_growth_pct
            >= REVENUE_SPIKE_THRESHOLD
        ):

            create_alert(
                run_id=run_id,
                alert_date=kpi_date,
                alert_type="REVENUE_SPIKE",
                severity="INFO",
                metric_name="revenue",
                actual_value=float(revenue),
                threshold_value=(
                    REVENUE_SPIKE_THRESHOLD
                ),
                change_pct=float(
                    revenue_growth_pct
                ),
                message=(
                    f"Revenue increased by "
                    f"{revenue_growth_pct:.2f}% "
                    f"on {kpi_date}, exceeding "
                    f"the {REVENUE_SPIKE_THRESHOLD:.0f}% "
                    "spike threshold."
                ),
            )

            alerts_generated += 1

    return alerts_generated


# ============================================================
# UPDATE WORKFLOW RUN
# ============================================================

def complete_workflow_run(
    run_id,
    started_at,
    alerts_generated
):

    completed_at = datetime.now()

    execution_seconds = (
        completed_at - started_at
    ).total_seconds()

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE analytics.workflow_runs
                SET
                    completed_at = %s,
                    status = %s,
                    alerts_generated = %s,
                    execution_seconds = %s
                WHERE run_id = %s;
                """,
                (
                    completed_at,
                    "SUCCESS",
                    alerts_generated,
                    execution_seconds,
                    run_id,
                )
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ============================================================
# SUMMARY
# ============================================================

def print_alert_summary(
    run_id,
    alerts_generated
):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    severity,
                    COUNT(*)
                FROM analytics.business_alerts
                WHERE run_id = %s
                GROUP BY severity
                ORDER BY severity;
                """,
                (run_id,)
            )

            severity_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    alert_date,
                    alert_type,
                    severity,
                    change_pct,
                    message
                FROM analytics.business_alerts
                WHERE run_id = %s
                ORDER BY alert_date;
                """,
                (run_id,)
            )

            alert_rows = cursor.fetchall()

    finally:

        connection.close()

    print()
    print("=" * 60)
    print("BUSINESS RULE ENGINE SUMMARY")
    print("=" * 60)

    print(
        f"Run ID: {run_id}"
    )

    print(
        f"Alerts generated: "
        f"{alerts_generated:,}"
    )

    print()
    print("BY SEVERITY")

    for severity, count in severity_rows:

        print(
            f"{severity}: {count:,}"
        )

    print()

    if not alert_rows:

        print("No business exceptions detected.")

    else:

        print("ALERTS")

        for (
            alert_date,
            alert_type,
            severity,
            change_pct,
            message,
        ) in alert_rows:

            print()
            print(
                f"[{severity}] "
                f"{alert_date} "
                f"{alert_type}"
            )

            print(
                f"Change: "
                f"{change_pct:.2f}%"
            )

            print(
                message
            )


# ============================================================
# MAIN
# ============================================================

def run_business_rules(run_id):

    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB")
    print("BUSINESS RULE ENGINE")
    print("=" * 60)

    started_at = datetime.now()

    print()
    print(
        f"Workflow run: {run_id}"
    )

    print()
    print("Loading KPI data...")

    kpi_rows = load_kpis()

    print(
        f"KPI records loaded: "
        f"{len(kpi_rows):,}"
    )

    clear_existing_alerts(
        run_id
    )

    print()
    print("Evaluating business rules...")

    alerts_generated = (
        evaluate_business_rules(
            run_id,
            kpi_rows
        )
    )

    print_alert_summary(
        run_id,
        alerts_generated
    )

    print()
    print("=" * 60)
    print("BUSINESS RULE ENGINE STATUS: SUCCESS")
    print("=" * 60)

    return alerts_generated

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    standalone_run_id, standalone_started_at = (
        create_workflow_run()
    )

    try:
        alerts_generated = run_business_rules(
            standalone_run_id
        )

        complete_workflow_run(
            standalone_run_id,
            standalone_started_at,
            alerts_generated
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("BUSINESS RULE ENGINE STATUS: FAILED")
        print("=" * 60)
        print(
            f"Error: {error}"
        )