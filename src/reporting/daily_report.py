from pathlib import Path
import os
from datetime import datetime

import pandas as pd
import psycopg2


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reports"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

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
            average_units_per_order,
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
            "No KPI records found."
        )

    columns = [
        "kpi_date",
        "revenue",
        "orders",
        "units_sold",
        "average_order_value",
        "average_units_per_order",
        "unique_customers",
        "revenue_growth_pct",
        "order_growth_pct",
    ]

    return dict(
        zip(columns, row)
    )


# ============================================================
# LOAD ALERTS FOR REPORTING DATE
# ============================================================

def load_alerts(report_date):

    connection = get_connection()

    query = """
        SELECT
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
        ORDER BY
            CASE severity
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'INFO' THEN 3
                ELSE 4
            END,
            alert_type;
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

    columns = [
        "alert_type",
        "severity",
        "metric_name",
        "actual_value",
        "threshold_value",
        "change_pct",
        "message",
        "status",
    ]

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# LOAD WORKFLOW STATUS
# ============================================================

def load_workflow_status():

    connection = get_connection()

    query = """
        SELECT
            status,
            files_discovered,
            files_processed,
            rows_received,
            rows_processed,
            error_count,
            warning_count,
            alerts_generated,
            execution_seconds,
            started_at,
            completed_at
        FROM analytics.workflow_runs
        ORDER BY started_at DESC
        LIMIT 1;
    """

    try:

        with connection.cursor() as cursor:

            cursor.execute(query)

            row = cursor.fetchone()

    finally:

        connection.close()

    if row is None:
        return {
            "status": "NOT AVAILABLE"
        }

    columns = [
        "status",
        "files_discovered",
        "files_processed",
        "rows_received",
        "rows_processed",
        "error_count",
        "warning_count",
        "alerts_generated",
        "execution_seconds",
        "started_at",
        "completed_at",
    ]

    return dict(
        zip(columns, row)
    )


# ============================================================
# BUILD REPORT DATA
# ============================================================

def build_report():

    kpi = load_latest_kpi()

    report_date = kpi["kpi_date"]

    alerts = load_alerts(
        report_date
    )

    workflow = load_workflow_status()

    return {
        "kpi": kpi,
        "alerts": alerts,
        "workflow": workflow,
    }


# ============================================================
# CSV REPORT
# ============================================================

def create_csv_report(report):

    kpi = report["kpi"]
    alerts = report["alerts"]
    workflow = report["workflow"]

    summary = pd.DataFrame([
        {
            "report_date": kpi["kpi_date"],
            "revenue": float(
                kpi["revenue"]
            ),
            "orders": int(
                kpi["orders"]
            ),
            "units_sold": int(
                kpi["units_sold"]
            ),
            "average_order_value": float(
                kpi["average_order_value"]
            ),
            "average_units_per_order": float(
                kpi["average_units_per_order"]
            ),
            "unique_customers": int(
                kpi["unique_customers"]
            ),
            "revenue_growth_pct": float(
                kpi["revenue_growth_pct"]
            ),
            "order_growth_pct": float(
                kpi["order_growth_pct"]
            ),
            "alert_count": len(alerts),
            "workflow_status": workflow.get(
                "status",
                "UNKNOWN"
            ),
        }
    ])

    output_path = (
        REPORT_DIR
        / "daily_sales_report.csv"
    )

    summary.to_csv(
        output_path,
        index=False
    )

    return output_path


# ============================================================
# HTML REPORT
# ============================================================

def create_html_report(report):

    kpi = report["kpi"]
    alerts = report["alerts"]
    workflow = report["workflow"]

    report_date = kpi["kpi_date"]

    generated_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # --------------------------------------------------------
    # ALERT HTML
    # --------------------------------------------------------

    if alerts:

        alert_rows = ""

        for alert in alerts:

            alert_rows += f"""
            <tr>
                <td>{alert["alert_type"]}</td>
                <td>{alert["severity"]}</td>
                <td>{alert["metric_name"]}</td>
                <td>{alert["change_pct"]:.2f}%</td>
                <td>{alert["status"]}</td>
                <td>{alert["message"]}</td>
            </tr>
            """

    else:

        alert_rows = """
        <tr>
            <td colspan="6">
                No business alerts detected for this date.
            </td>
        </tr>
        """

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>Daily Sales Automation Report</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    background: #f5f7fa;
    color: #1f2937;
}}

.container {{
    max-width: 1200px;
    margin: auto;
}}

.header {{
    background: #111827;
    color: white;
    padding: 28px;
    border-radius: 12px;
    margin-bottom: 24px;
}}

.header h1 {{
    margin: 0 0 8px 0;
}}

.header p {{
    margin: 4px 0;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}

.card {{
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow:
        0 2px 8px rgba(0,0,0,0.08);
}}

.card-title {{
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 8px;
}}

.card-value {{
    font-size: 25px;
    font-weight: bold;
}}

.section {{
    background: white;
    padding: 24px;
    border-radius: 10px;
    margin-bottom: 24px;
    box-shadow:
        0 2px 8px rgba(0,0,0,0.08);
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}}

th {{
    background: #f3f4f6;
}}

.success {{
    font-weight: bold;
}}

.alert {{
    color: #b91c1c;
    font-weight: bold;
}}

.footer {{
    color: #6b7280;
    font-size: 12px;
    margin-top: 20px;
}}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>Daily Sales Automation Report</h1>

<p>
Reporting Date:
<strong>{report_date}</strong>
</p>

<p>
Generated:
{generated_at}
</p>

</div>


<div class="grid">

<div class="card">
<div class="card-title">
Revenue
</div>
<div class="card-value">
AED {float(kpi["revenue"]):,.2f}
</div>
</div>


<div class="card">
<div class="card-title">
Orders
</div>
<div class="card-value">
{int(kpi["orders"]):,}
</div>
</div>


<div class="card">
<div class="card-title">
Units Sold
</div>
<div class="card-value">
{int(kpi["units_sold"]):,}
</div>
</div>


<div class="card">
<div class="card-title">
Average Order Value
</div>
<div class="card-value">
AED {float(kpi["average_order_value"]):,.2f}
</div>
</div>

</div>


<div class="grid">

<div class="card">
<div class="card-title">
Unique Customers
</div>
<div class="card-value">
{int(kpi["unique_customers"]):,}
</div>
</div>


<div class="card">
<div class="card-title">
Revenue Growth
</div>
<div class="card-value">
{float(kpi["revenue_growth_pct"]):.2f}%
</div>
</div>


<div class="card">
<div class="card-title">
Order Growth
</div>
<div class="card-value">
{float(kpi["order_growth_pct"]):.2f}%
</div>
</div>


<div class="card">
<div class="card-title">
Business Alerts
</div>
<div class="card-value">
{len(alerts):,}
</div>
</div>

</div>


<div class="section">

<h2>Business Alerts</h2>

<table>

<thead>

<tr>
<th>Alert Type</th>
<th>Severity</th>
<th>Metric</th>
<th>Change</th>
<th>Status</th>
<th>Message</th>
</tr>

</thead>

<tbody>

{alert_rows}

</tbody>

</table>

</div>


<div class="section">

<h2>Workflow Execution</h2>

<table>

<tr>
<th>Metric</th>
<th>Value</th>
</tr>

<tr>
<td>Status</td>
<td class="success">
{workflow.get("status", "UNKNOWN")}
</td>
</tr>

<tr>
<td>Files Discovered</td>
<td>
{workflow.get("files_discovered", 0):,}
</td>
</tr>

<tr>
<td>Files Processed</td>
<td>
{workflow.get("files_processed", 0):,}
</td>
</tr>

<tr>
<td>Rows Received</td>
<td>
{workflow.get("rows_received", 0):,}
</td>
</tr>

<tr>
<td>Rows Processed</td>
<td>
{workflow.get("rows_processed", 0):,}
</td>
</tr>

<tr>
<td>Errors</td>
<td>
{workflow.get("error_count", 0):,}
</td>
</tr>

<tr>
<td>Warnings</td>
<td>
{workflow.get("warning_count", 0):,}
</td>
</tr>

<tr>
<td>Alerts Generated</td>
<td>
{workflow.get("alerts_generated", 0):,}
</td>
</tr>

<tr>
<td>Execution Time</td>
<td>
{float(workflow.get("execution_seconds", 0) or 0):.2f}
seconds
</td>
</tr>

</table>

</div>


<div class="footer">

Workflow Automation Hub —
Automated Daily Sales Monitoring & Exception Detection

</div>

</div>

</body>

</html>
"""

    output_path = (
        REPORT_DIR
        / "daily_sales_report.html"
    )

    output_path.write_text(
        html,
        encoding="utf-8"
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

def run_report():

    print("=" * 60)
    print("WORKFLOW AUTOMATION HUB")
    print("AUTOMATED DAILY REPORT")
    print("=" * 60)

    print()
    print("Loading business data...")

    report = build_report()

    kpi = report["kpi"]

    print(
        f"Reporting date: "
        f"{kpi['kpi_date']}"
    )

    print(
        f"Revenue: "
        f"AED {float(kpi['revenue']):,.2f}"
    )

    print(
        f"Orders: "
        f"{int(kpi['orders']):,}"
    )

    print(
        f"Units sold: "
        f"{int(kpi['units_sold']):,}"
    )

    print(
        f"Average order value: "
        f"AED {float(kpi['average_order_value']):,.2f}"
    )

    print(
        f"Revenue growth: "
        f"{float(kpi['revenue_growth_pct']):.2f}%"
    )

    print(
        f"Order growth: "
        f"{float(kpi['order_growth_pct']):.2f}%"
    )

    print(
        f"Business alerts: "
        f"{len(report['alerts']):,}"
    )

    print()
    print("Generating CSV report...")

    csv_path = create_csv_report(
        report
    )

    print(
        f"CSV created: {csv_path}"
    )

    print()
    print("Generating HTML report...")

    html_path = create_html_report(
        report
    )

    print(
        f"HTML created: {html_path}"
    )

    print()
    print("=" * 60)
    print("REPORT GENERATION STATUS: SUCCESS")
    print("=" * 60)


if __name__ == "__main__":

    run_report()