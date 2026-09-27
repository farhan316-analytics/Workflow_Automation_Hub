import os
import uuid
from datetime import date

import psycopg2


DB_CONFIG = {
    "host": os.getenv("WORKFLOW_DB_HOST", "localhost"),
    "port": os.getenv("WORKFLOW_DB_PORT", "5432"),
    "dbname": os.getenv("WORKFLOW_DB_NAME", "workflow_automation"),
    "user": os.getenv("WORKFLOW_DB_USER", "postgres"),
    "password": os.getenv("WORKFLOW_DB_PASSWORD"),
}


TEST_DATE = date(2099, 12, 31)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_controlled_kpi():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM analytics.daily_kpis
                WHERE kpi_date = %s;
                """,
                (TEST_DATE,)
            )

            cursor.execute(
                """
                INSERT INTO analytics.daily_kpis (
                    kpi_date,
                    revenue,
                    orders,
                    units_sold,
                    average_order_value,
                    average_units_per_order,
                    unique_customers,
                    revenue_growth_pct,
                    order_growth_pct
                )
                VALUES (
                    %s,
                    50000.00,
                    100,
                    200,
                    500.00,
                    2.00,
                    95,
                    -50.00,
                    0.00
                );
                """,
                (TEST_DATE,)
            )

        connection.commit()

    finally:
        connection.close()


def verify_alert():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    alert_id,
                    alert_date,
                    alert_type,
                    severity,
                    metric_name,
                    actual_value,
                    threshold_value,
                    change_pct,
                    message,
                    status
                FROM analytics.business_alerts
                WHERE alert_date = %s
                ORDER BY created_at DESC;
                """,
                (TEST_DATE,)
            )

            alerts = cursor.fetchall()

            if not alerts:
                print("\n❌ ALERT PATH TEST FAILED")
                print(
                    "No alert was generated for the "
                    "controlled revenue decline."
                )
                return False

            print("\n" + "=" * 70)
            print("🚨 CONTROLLED ALERT TEST")
            print("=" * 70)

            for alert in alerts:

                print(f"Alert ID:        {alert[0]}")
                print(f"Alert Date:      {alert[1]}")
                print(f"Alert Type:      {alert[2]}")
                print(f"Severity:        {alert[3]}")
                print(f"Metric:          {alert[4]}")
                print(f"Actual Value:    {alert[5]}")
                print(f"Threshold:       {alert[6]}")
                print(f"Change:          {alert[7]}%")
                print(f"Message:         {alert[8]}")
                print(f"Status:          {alert[9]}")
                print("-" * 70)

            high_revenue_alert = any(
                alert[3] == "HIGH"
                and alert[4] == "revenue"
                for alert in alerts
            )

            if high_revenue_alert:
                print("✅ HIGH revenue-decline alert detected.")
                return True

            print("❌ Expected HIGH revenue alert was not found.")
            return False

    finally:
        connection.close()


def cleanup(qa_run_id=None):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM analytics.business_alerts
                WHERE alert_date = %s;
                """,
                (TEST_DATE,)
            )

            cursor.execute(
                """
                DELETE FROM analytics.daily_kpis
                WHERE kpi_date = %s;
                """,
                (TEST_DATE,)
            )

            if qa_run_id is not None:

                cursor.execute(
                    """
                    DELETE FROM analytics.workflow_runs
                    WHERE run_id = %s;
                    """,
                    (qa_run_id,)
                )

        connection.commit()

    finally:
        connection.close()


def main():

    qa_run_id = None
    passed = False

    print("=" * 70)
    print("WORKFLOW AUTOMATION HUB")
    print("ALERT-PATH QA TEST")
    print("=" * 70)

    try:

        print("\n1. Creating controlled revenue-drop KPI...")

        create_controlled_kpi()

        print("   ✅ Controlled KPI created.")

        print("\n2. Running business-rule engine...")

        from src.rules.business_rules import (
            create_workflow_run,
            run_business_rules,
            complete_workflow_run,
        )

        qa_run_id = str(uuid.uuid4())

        qa_run_id, qa_started_at = create_workflow_run(
        qa_run_id
   ) 

        alerts_generated = run_business_rules(
        qa_run_id
        )

        complete_workflow_run(
            qa_run_id,
            qa_started_at,
            alerts_generated
        )

        print("   ✅ Business-rule engine completed.")

        print("\n3. Checking for generated alert...")

        passed = verify_alert()

    except Exception as error:

        print("\n❌ QA TEST ERROR")
        print(f"Error: {error}")

    finally:

        print("\n4. Cleaning up QA data...")

        cleanup(qa_run_id)

        print("   ✅ QA data removed.")

    print("\n" + "=" * 70)

    if passed:
        print("✅ ALERT-PATH QA TEST: PASS")
    else:
        print("❌ ALERT-PATH QA TEST: FAIL")

    print("=" * 70)


if __name__ == "__main__":
    main()