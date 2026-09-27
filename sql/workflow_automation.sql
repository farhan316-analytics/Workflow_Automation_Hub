SELECT
    run_id,
    workflow_name,
    status,
    error_message,
    started_at,
    completed_at
FROM analytics.workflow_runs
ORDER BY started_at DESC
LIMIT 5;