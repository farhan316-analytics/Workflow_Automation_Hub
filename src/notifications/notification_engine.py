from pathlib import Path
import os
import smtplib
from email.message import EmailMessage
import psycopg2


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reports"
)


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
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv(
    "WORKFLOW_SMTP_HOST"
)

SMTP_PORT = int(
    os.getenv(
        "WORKFLOW_SMTP_PORT",
        "587"
    )
)

SMTP_USER = os.getenv(
    "WORKFLOW_SMTP_USER"
)

SMTP_PASSWORD = os.getenv(
    "WORKFLOW_SMTP_PASSWORD"
)

NOTIFICATION_TO = os.getenv(
    "WORKFLOW_NOTIFICATION_TO"
)


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
# LOAD LATEST KPI
# ============================================================

def load_latest_kpi():

    connection = get_connection()

    query = """
        SELECT
            kpi_date,
            revenue,
            orders,
            units_sold,
            average_order_value,
            unique_customers,
            revenue_growth_pct,
            order_growth_pct
        FROM analytics.daily_kpis
        ORDER BY kpi_date DESC
        LIMIT 1;
    """

    try:

        with connection.cursor() as cursor:

            cursor.execute(query)

            row = cursor.fetchone()

    finally:

        connection.close()

    if row is None:
        raise ValueError(
            "No KPI data found."
        )

    return {
        "date": row[0],
        "revenue": float(row[1]),
        "orders": int(row[2]),
        "units_sold": int(row[3]),
        "average_order_value": float(row[4]),
        "unique_customers": int(row[5]),
        "revenue_growth_pct": float(row[6]),
        "order_growth_pct": float(row[7]),
    }


# ============================================================
# LOAD LATEST ALERTS
# ============================================================

def load_latest_alerts(report_date):

    connection = get_connection()

    query = """
        SELECT
            alert_type,
            severity,
            metric_name,
            change_pct,
            message
        FROM analytics.business_alerts
        WHERE alert_date = %s
        ORDER BY
            CASE severity
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'INFO' THEN 3
                ELSE 4
            END;
    """

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                query,
                (report_date,)
            )

            rows = cursor.fetchall()

    finally:

        connection.close()

    return [
        {
            "alert_type": row[0],
            "severity": row[1],
            "metric_name": row[2],
            "change_pct": float(row[3]),
            "message": row[4],
        }
        for row in rows
    ]


# ============================================================
# BUILD NOTIFICATION MESSAGE
# ============================================================

def build_notification():

    kpi = load_latest_kpi()

    alerts = load_latest_alerts(
        kpi["date"]
    )

    if alerts:

        status = "ACTION REQUIRED"

    else:

        status = "NO BUSINESS EXCEPTIONS"

    lines = []

    lines.append(
        "🚨 DAILY SALES AUTOMATION SUMMARY"
    )

    lines.append(
        "=" * 50
    )

    lines.append(
        f"Date: {kpi['date']}"
    )

    lines.append(
        f"Status: {status}"
    )

    lines.append("")

    lines.append(
        "BUSINESS PERFORMANCE"
    )

    lines.append(
        f"Revenue: "
        f"AED {kpi['revenue']:,.2f}"
    )

    lines.append(
        f"Revenue Growth: "
        f"{kpi['revenue_growth_pct']:.2f}%"
    )

    lines.append(
        f"Orders: "
        f"{kpi['orders']:,}"
    )

    lines.append(
        f"Order Growth: "
        f"{kpi['order_growth_pct']:.2f}%"
    )

    lines.append(
        f"Units Sold: "
        f"{kpi['units_sold']:,}"
    )

    lines.append(
        f"Average Order Value: "
        f"AED {kpi['average_order_value']:,.2f}"
    )

    lines.append(
        f"Unique Customers: "
        f"{kpi['unique_customers']:,}"
    )

    lines.append("")

    lines.append(
        f"BUSINESS ALERTS: {len(alerts)}"
    )

    if alerts:

        lines.append("")

        for alert in alerts:

            lines.append(
                f"[{alert['severity']}] "
                f"{alert['alert_type']}"
            )

            lines.append(
                f"Change: "
                f"{alert['change_pct']:.2f}%"
            )

            lines.append(
                alert["message"]
            )

            lines.append("")

    else:

        lines.append(
            "No business exceptions detected."
        )

    lines.append(
        "REPORT"
    )

    html_report = (
        REPORT_DIR
        / "daily_sales_report.html"
    )

    lines.append(
        f"HTML report: {html_report}"
    )

    return "\n".join(lines)


# ============================================================
# CONSOLE NOTIFICATION
# ============================================================

def send_console_notification(
    message
):

    print()
    print("=" * 60)
    print("NOTIFICATION")
    print("=" * 60)
    print()
    print(message)
    print()
    print("=" * 60)
    print(
        "Console notification: SENT"
    )
    print("=" * 60)


# ============================================================
# EMAIL NOTIFICATION
# ============================================================

def send_email_notification(
    message
):

    missing = []

    if not SMTP_HOST:
        missing.append(
            "WORKFLOW_SMTP_HOST"
        )

    if not SMTP_USER:
        missing.append(
            "WORKFLOW_SMTP_USER"
        )

    if not SMTP_PASSWORD:
        missing.append(
            "WORKFLOW_SMTP_PASSWORD"
        )

    if not NOTIFICATION_TO:
        missing.append(
            "WORKFLOW_NOTIFICATION_TO"
        )

    if missing:

        print()
        print(
            "Email notification: SKIPPED"
        )

        print(
            "Missing configuration: "
            + ", ".join(missing)
        )

        return False

    email = EmailMessage()

    email["Subject"] = (
        "Daily Sales Automation Summary"
    )

    email["From"] = SMTP_USER
    email["To"] = NOTIFICATION_TO

    email.set_content(
        message
    )

    try:

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD
            )

            server.send_message(
                email
            )

        print()
        print(
            "Email notification: SENT"
        )

        return True

    except Exception as error:

        print()
        print(
            "Email notification: FAILED"
        )

        print(
            f"Reason: {error}"
        )

        return False


# ============================================================
# MAIN
# ============================================================

def run_notification_engine():

    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB")
    print("NOTIFICATION ENGINE")
    print("=" * 60)

    message = build_notification()

    # Always provide a console notification.
    send_console_notification(
        message
    )

    # Email is optional.
    send_email_notification(
        message
    )

    print()
    print("=" * 60)
    print(
        "NOTIFICATION ENGINE STATUS: SUCCESS"
    )
    print("=" * 60)


if __name__ == "__main__":

    run_notification_engine()