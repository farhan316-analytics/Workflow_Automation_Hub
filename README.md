# 🤖 Workflow Automation Hub

## 🚀 Automated Retail Sales Monitoring, KPI Intelligence & Business Exception Detection

> **Automate the workflow. Detect the exception. Deliver the insight.**

Workflow Automation Hub is an end-to-end business data automation platform designed to transform daily retail sales files into validated data, PostgreSQL analytics, business KPIs, automated reports, notifications, and rule-based business alerts.

The project demonstrates how a Business/Data Analyst can move beyond static dashboards and build a repeatable analytical workflow that automatically processes incoming data, validates data quality, calculates business performance, detects exceptions, generates management reports, and records workflow execution history.

---

# 🎯 Project Overview

Retail businesses receive sales data continuously, but manually processing files, checking data quality, calculating KPIs, identifying unusual performance, and preparing reports can become repetitive and error-prone.

**Workflow Automation Hub automates this entire process.**

```text
📄 Daily Sales CSV
        │
        ▼
📥 File Ingestion
        │
        ▼
🔎 Data Validation
        │
        ▼
⚙️ ETL Transformation
        │
        ▼
🐘 PostgreSQL
        │
        ▼
📊 KPI Engine
        │
        ▼
🚨 Business Rules
        │
        ├──────────────────┐
        ▼                  ▼
   Normal Performance   Business Exception
        │                  │
        ▼                  ▼
   📄 Daily Report      🚨 Business Alert
        │                  │
        └────────┬─────────┘
                 ▼
          📢 Notification
                 │
                 ▼
        📝 Workflow Audit Log

``` 


The system was designed to demonstrate the ability to:
- 🔄 Automate repetitive business data workflows
- 🔎 Validate incoming business data
- ⚙️ Build a reusable ETL pipeline
- 🐘 Store analytical data in PostgreSQL
- 📊 Calculate daily business KPIs
- 🚨 Apply rule-based business monitoring
- 📉 Detect significant revenue declines
- 📄 Generate automated management reports
- 📢 Produce automated notifications
- 📝 Maintain workflow execution history
- 🛡️ Handle workflow failures safely
- 🧪 Build controlled QA tests
- 🔐 Separate production data from QA scenarios
💼 Business Problem
A typical retail analytics process may require an analyst to manually:
1. 📥 Receive daily sales files
2. 🔎 Check whether files are complete
3. ⚠️ Look for duplicates or invalid values
4. 🧹 Clean and transform the data
5. 🐘 Load the data into a database
6. 📊 Calculate daily KPIs
7. 📈 Compare current performance with previous periods
8. 🚨 Identify significant business changes
9. 📄 Prepare a report
10. 📢 Notify stakeholders
This creates potential problems such as:
- ⏱️ Repetitive manual work
- 🐌 Delayed reporting
- ❌ Inconsistent validation
- 🧮 Manual calculation errors
- 🚨 Missed business exceptions
- 🔍 Poor workflow traceability
Workflow Automation Hub converts this process into an automated analytical workflow.
🏗️ Core Architecture

### 📥 1. File Ingestion
The ingestion module discovers incoming production sales files using:
sales_YYYY-MM-DD.csv

Production files are processed automatically.
QA files beginning with:
test_

are excluded from the normal production workflow.
This prevents controlled test scenarios from contaminating production processing.
### 🔎 2. Data Validation
The validation engine checks incoming files before they enter the analytical pipeline.
Validation Checks
- 📋 Required columns
- 📭 Empty-file detection
- 🔁 Duplicate transaction IDs
- ❓ Missing critical values
- 🔢 Numeric field validation
- ➖ Negative value detection
- 📅 Date validation
- 💳 Payment method validation
- 🛒 Sales channel validation
🧪 Controlled QA Files
test_valid.csv
test_duplicate.csv
test_missing_column.csv
test_missing_values.csv
test_invalid_amount.csv
test_revenue_drop.csv

❌ Validation Failure
Examples:
Missing required column
Invalid negative revenue
Invalid data type

⚠️ Validation Warning
Examples:
Duplicate transaction IDs
Missing non-critical values

📈 Valid Business Scenario
A revenue decline is not automatically considered a data-quality problem.
For example:
Revenue declined by 25%

could represent a legitimate business situation.
Therefore, the project separates:
🔎 DATA QUALITY RULES

from:
📊 BUSINESS PERFORMANCE RULES

### ⚙️ 3. ETL Transformation
Validated sales data is transformed before database loading.
The transformation layer performs:
- 🧹 Column normalization
- 📅 Date parsing
- 🔢 Numeric conversion
- ✂️ Text cleaning
- 🔁 Duplicate transaction handling
- 💰 Gross amount recalculation
- 🏷️ Discount amount recalculation
- 💵 Net revenue recalculation
- 📅 Date dimension creation
- 🗓️ Weekend identification
- 🛒 Order value calculation
- 📦 Revenue-per-unit calculation
- 🔢 Sorting and standardized output
Additional fields:
year
month
month_name
day
day_of_week
is_weekend
order_value
revenue_per_unit

Processed files are stored in:
data/processed/

### 🐘 4. PostgreSQL Analytics Database
The project uses PostgreSQL as the central analytical database.
Database
workflow_automation

Schema
analytics

🧾 analytics.sales_transactions
Stores transaction-level sales data.
Key fields include:
transaction_id
transaction_date
store_id
region
customer_id
product_id
product_name
category
quantity
unit_price
discount_pct
gross_amount
discount_amount
net_revenue
payment_method
sales_channel
year
month
month_name
day
day_of_week
is_weekend
order_value
revenue_per_unit
loaded_at

📊 analytics.daily_kpis
Stores daily business performance metrics.
Metrics include:
revenue
orders
units_sold
average_order_value
average_units_per_order
unique_customers
revenue_growth_pct
order_growth_pct

📝 analytics.workflow_runs
Tracks workflow execution history.
Tracked information includes:
run_id
workflow_name
started_at
completed_at
status
files_discovered
files_processed
rows_received
rows_processed
error_count
warning_count
alerts_generated
execution_seconds
error_message

This provides workflow observability.
🚨 analytics.business_alerts
Stores detected business exceptions.
Key fields:
alert_id
run_id
alert_date
alert_type
severity
metric_name
actual_value
threshold_value
change_pct
message
status
created_at

### 📊 5. KPI Engine

The KPI engine automatically calculates daily business performance.
💰 Revenue
Total daily net sales.
🧾 Orders
Number of transactions.
📦 Units Sold
Total quantity sold.
🛒 Average Order Value
Revenue / Orders

📦 Average Units Per Order
Units Sold / Orders

👥 Unique Customers
Distinct customer count.
📈 Revenue Growth
Comparison of current revenue with the previous day.
📈 Order Growth
Comparison of current order volume with the previous day.

### 🚨 6. Business Rule Engine

The business rule engine evaluates daily KPIs against predefined thresholds.
🔴 Revenue Decline
Revenue decline <= -20%

Severity:
HIGH

Example:
Revenue Growth = -50%
Threshold = -20%

Result:
🔴 HIGH — REVENUE_DECLINE

🟠 Order Decline
Order decline <= -15%

Severity:
MEDIUM

🔵 Revenue Spike
Revenue increase >= +30%

Severity:
INFO

🧠 Business Rule Philosophy
The system deliberately separates:
🔎 DATA QUALITY

from:
📊 BUSINESS PERFORMANCE

For example:
Negative revenue
       ↓
❌ Data Quality Failure

while:
30% revenue decline
       ↓
🚨 Business Exception

This distinction prevents legitimate business problems from being incorrectly classified as corrupted data.

### 📄 7. Automated Reporting

The reporting engine generates daily management reports.
Output
data/processed/reports/daily_sales_report.csv
data/processed/reports/daily_sales_report.html

The report includes:
- 📅 Reporting date
- 💰 Revenue
- 📈 Revenue growth
- 🧾 Orders
- 📈 Order growth
- 📦 Units sold
- 🛒 Average order value
- 👥 Unique customers
- 🚨 Business alert count
- ⚠️ Alert details
- 📝 Workflow status

### 📢 8. Notification Engine

The notification engine generates an automated daily sales summary.
Example:
🚨 DAILY SALES AUTOMATION SUMMARY
==================================

Date: 2026-09-23
Status: NO BUSINESS EXCEPTIONS

BUSINESS PERFORMANCE

Revenue: AED 2,762,578.89
Revenue Growth: 6.27%
Orders: 2,270
Order Growth: 2.76%
Units Sold: 4,379
Average Order Value: AED 1,217.00
Unique Customers: 1,969

Business Alerts: 0

📧 Email Notifications
Email notifications are supported through optional SMTP configuration.
If SMTP credentials are unavailable, the system safely skips email delivery rather than failing the analytical workflow.

### 🤖 9. Workflow Orchestrator

The central orchestrator is:
src/workflow_runner.py

It coordinates the entire pipeline:
🚀 Workflow Start
       ↓
📥 File Discovery
       ↓
🔎 Validation
       ↓
⚙️ ETL
       ↓
🐘 Database Loading
       ↓
📊 KPI Calculation
       ↓
🚨 Business Rules
       ↓
📄 Report Generation
       ↓
📢 Notification
       ↓
📝 Workflow Completion

Every orchestration execution receives a unique workflow ID.
Example:
95cf96fc-1129-452c-9809-22535d6098ba

The same workflow ID is used throughout the parent workflow audit lifecycle.

### 📝 Workflow Audit Architecture

The orchestrator owns the parent workflow execution.
A complete workflow creates one parent record:
Workflow Automation Hub

with a status:
RUNNING
SUCCESS
FAILED

This creates traceability between:
Workflow
   ↓
Processing
   ↓
KPIs
   ↓
Business Rules
   ↓
Alerts

### 🛡️ Error Handling
The workflow distinguishes between successful and failed execution.
If a workflow stage raises an exception:
💥 Exception
     ↓
📝 Workflow audit updated
     ↓
❌ Status = FAILED
     ↓
📄 Error message recorded

The workflow does not silently report a failed execution as successful.
A controlled QA failure verified:
Status: FAILED
Error Message: CONTROLLED QA FAILURE TEST

The workflow was subsequently restored and successfully executed again.

### 🔄 Data Reconciliation

The production dataset contains:
120,000 transactions
120,000 unique transactions

Production date coverage:
2026-08-01
      ↓
2026-09-23

Total transaction revenue:
AED 14,019,820.20

Revenue Reconciliation
Transaction Revenue = AED 14,019,820.20
KPI Revenue         = AED 14,019,820.20
Difference           = AED 0.00

✅ Transaction-level revenue reconciles exactly with the KPI layer.
📈 Example Business Performance
Latest verified production KPI example:
KPI	Value
📅 Date	2026-09-23
💰 Revenue	AED 2,762,578.89
📈 Revenue Growth	6.27%
🧾 Orders	2,270
📈 Order Growth	2.76%
📦 Units Sold	4,379
🛒 Average Order Value	AED 1,217.00
👥 Unique Customers	1,969
🚨 Business Alerts	0


🧪 Controlled Business Exception Test
The project includes a dedicated alert-path QA test.
A controlled scenario was created:
Revenue Growth = -50.00%
Business Threshold = -20.00%

The business rule engine automatically generated:
Alert Type: REVENUE_DECLINE
Severity: HIGH
Metric: revenue
Change: -50.00%
Status: OPEN

The temporary QA records were then removed.
Result
✅ ALERT-PATH QA TEST: PASS

This proves that the system can detect a business exception rather than only process successful data.

### 🧪 QA & Testing

The project includes controlled QA scenarios covering:
- 📥 File discovery
- 📄 Valid file processing
- ❌ Missing columns
- 🔁 Duplicate transactions
- ❓ Missing values
- ➖ Invalid revenue
- ⚙️ ETL transformations
- 🐘 PostgreSQL loading
- 🔐 Transaction uniqueness
- 💰 Revenue reconciliation
- 📊 KPI calculations
- 🚨 Business rule evaluation
- 📉 Revenue-decline alerts
- 🔴 Alert severity
- 🎯 Alert thresholds
- 📄 Report generation
- 🌐 HTML report generation
- 📢 Notification generation
- 📧 SMTP configuration handling
- 🤖 Workflow orchestration
- 🔐 Production/test separation
- 📝 Workflow audit logging
- ⏱️ Workflow timestamps
- 📊 Execution tracking
- 🧹 QA data cleanup
- 🔄 Workflow reruns
- 💥 Failure handling
- 🔗 End-to-end execution

### 🏆 Final QA Result

╔══════════════════════════════════╗
║       FINAL QA RESULT            ║
╠══════════════════════════════════╣
║          40 / 40 PASS            ║
║                                  ║
║       100% QA PASS RATE          ║
╚══════════════════════════════════╝

The final QA process verified both:
✅ SUCCESS PATH

and:
❌ FAILURE PATH

### 📁 Project Structure
Workflow_Automation_Hub/
│
├── 📂 data/
│   ├── 📂 incoming/
│   │   ├── sales_YYYY-MM-DD.csv
│   │   ├── test_valid.csv
│   │   ├── test_duplicate.csv
│   │   ├── test_missing_column.csv
│   │   ├── test_missing_values.csv
│   │   ├── test_invalid_amount.csv
│   │   └── test_revenue_drop.csv
│   │
│   └── 📂 processed/
│       ├── processed_sales_YYYY-MM-DD.csv
│       └── 📂 reports/
│           ├── daily_sales_report.csv
│           └── daily_sales_report.html
│
├── 📂 src/
│   ├── 📂 ingestion/
│   │   └── file_ingestion.py
│   │
│   ├── 📂 validation/
│   │   └── data_validator.py
│   │
│   ├── 📂 transformation/
│   │   └── sales_transformer.py
│   │
│   ├── 📂 database/
│   │   └── db_loader.py
│   │
│   ├── 📂 analytics/
│   │   └── kpi_engine.py
│   │
│   ├── 📂 rules/
│   │   └── business_rules.py
│   │
│   ├── 📂 reporting/
│   │   └── daily_report.py
│   │
│   ├── 📂 notifications/
│   │   └── notification_engine.py
│   │
│   ├── 📂 qa/
│   │   ├── test_alert_path.py
│   │   └── test_failure_handling.py
│   │
│   └── workflow_runner.py
│
├── 📄 README.md
└── 📄 requirements.txt

### 🛠️ Technology Stack

Category	                Technology
🐍 Programming          	Python
🧹 Data Processing	        Pandas
🐘 Database             	PostgreSQL
🔌 Database Driver	        Psycopg2
📊 Analytics	            Python / SQL
📄 Reporting	            HTML / CSV
🤖 Automation           	Python Workflow Orchestration
🧪 Testing	                Controlled QA Scripts
📝 Audit	                PostgreSQL Workflow Logging


### 🔐 Environment Variables

Database configuration uses environment variables.
PowerShell
$env:WORKFLOW_DB_HOST="localhost"
$env:WORKFLOW_DB_PORT="5432"
$env:WORKFLOW_DB_NAME="workflow_automation"
$env:WORKFLOW_DB_USER="postgres"
$env:WORKFLOW_DB_PASSWORD="YOUR_POSTGRES_PASSWORD"

Optional SMTP Configuration
$env:WORKFLOW_SMTP_HOST="YOUR_SMTP_HOST"
$env:WORKFLOW_SMTP_PORT="587"
$env:WORKFLOW_SMTP_USER="YOUR_SMTP_USER"
$env:WORKFLOW_SMTP_PASSWORD="YOUR_SMTP_PASSWORD"
$env:WORKFLOW_NOTIFICATION_TO="YOUR_EMAIL"

⚠️ Never commit database passwords, SMTP credentials, API keys, or other secrets to GitHub.

### 🚀 Installation
Clone the repository:
git clone https://github.com/farhan316-analytics/Workflow_Automation_Hub.git

Navigate to the project:
cd Workflow_Automation_Hub

Install dependencies:
pip install -r requirements.txt

Configure PostgreSQL and the required environment variables.

### ▶️ Running the Workflow

Run the complete production workflow:
python -m src.workflow_runner

Expected final result:
FINAL STATUS: SUCCESS

🧪 Running QA Tests
🚨 Alert Path Test
python -m src.qa.test_alert_path

Expected:
✅ ALERT-PATH QA TEST: PASS

💥 Failure Handling Test
python -m src.qa.test_failure_handling

Expected:
✅ FAILURE-HANDLING QA TEST: PASS

🗄️ Database Verification
Workflow Audit
SELECT
    run_id,
    workflow_name,
    started_at,
    completed_at,
    status,
    files_discovered,
    files_processed,
    rows_received,
    rows_processed,
    error_count,
    warning_count,
    alerts_generated,
    execution_seconds,
    error_message
FROM analytics.workflow_runs
ORDER BY started_at DESC;

Business Alerts
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
ORDER BY created_at DESC;

### 🧠 Design Principles

1️⃣ Separate Data Quality from Business Performance
A legitimate revenue decline should not automatically be treated as corrupted data.
🔎 Data Validation
        ≠
📊 Business Monitoring

2️⃣ Automate Repetitive Analytical Work
The workflow minimizes manual intervention in:
- 📥 File processing
- 📊 KPI calculations
- 🚨 Business monitoring
- 📄 Report creation
- 📢 Notifications
- 📝 Workflow tracking
3️⃣ Make Failures Visible
A failed workflow should never silently appear successful.
SUCCESS

or:
FAILED

with the corresponding error message.
4️⃣ Build for Traceability
Every workflow execution receives a unique ID.
This creates a traceable connection between:
Workflow
   ↓
Processing
   ↓
KPIs
   ↓
Business Rules
   ↓
Alerts

5️⃣ Test Business Scenarios
The project tests not only code behavior, but business scenarios:
- ❌ Invalid data
- 🔁 Duplicate data
- ❓ Missing data
- 📉 Revenue decline
- 💥 Workflow failure
💡 What This Project Demonstrates
📊 Business/Data Analyst Skills
- Data ingestion
- Data validation
- ETL
- SQL
- PostgreSQL
- KPI development
- Business rules
- Exception monitoring
- Automated reporting
- Workflow automation
- Data reconciliation
- QA testing

### 💻 Technical Skills

- Python
- Pandas
- PostgreSQL
- Psycopg2
- Modular architecture
- Database integration
- Environment-based configuration
- Workflow state management
- Error handling
- Automated exception detection
- Controlled testing
- Audit logging
🔮 Future Enhancements
Potential future improvements include:
- 📊 Power BI monitoring dashboard
- ⏰ Windows Task Scheduler integration
- ☁️ Cloud deployment
- 🔄 Apache Airflow orchestration
- 📧 Email notifications
- 💬 Microsoft Teams / Slack notifications
- ⚙️ Configurable business-rule thresholds
- 🤖 Advanced anomaly detection
- 📈 Forecast-based alerting
- 🏪 Store-level performance monitoring
- 📦 Product-level exception monitoring
- 👥 Role-based notification routing
- 📊 Workflow execution dashboard
- 🚨 Historical alert analytics

### 🏆 Project Outcome

Workflow Automation Hub successfully demonstrates an automated business analytics workflow that can:
📥 Ingest
   ↓
🔎 Validate
   ↓
⚙️ Transform
   ↓
🐘 Store
   ↓
📊 Analyze
   ↓
🚨 Detect
   ↓
📄 Report
   ↓
📢 Notify
   ↓
📝 Audit

📌 Verified Results
120,000 Production Transactions
120,000 Unique Transactions
AED 14,019,820.20 Reconciled Revenue
40/40 QA Tests Passed
100% Functional QA Pass Rate

The project successfully demonstrated:
✅ Normal Workflow
       ↓
    SUCCESS

📉 Business Exception
       ↓
   HIGH ALERT

💥 System Failure
       ↓
FAILED + ERROR RECORDED

This makes Workflow Automation Hub a practical demonstration of:
Business Intelligence + Data Analytics + ETL + Workflow Automation + Business Exception Monitoring

### 👨‍💻 Author
Mohammad Farhan
MBA — Business Analytics & AI
Middlesex University Dubai
Business Data Analyst | Business Intelligence | Data Analytics | Automation

### 🔗 Links

- 💻 GitHub: https://github.com/farhan316-analytics
- 🌐 Portfolio: https://farhan-analytics.lovable.app/

### 📜 License

This project is intended for portfolio and educational demonstration purposes.
Synthetic sales data and controlled QA scenarios are used to demonstrate the workflow architecture and business-monitoring capabilities.