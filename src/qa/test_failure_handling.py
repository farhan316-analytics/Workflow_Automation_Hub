import os
import psycopg2

import src.workflow_runner as workflow_runner


DB_CONFIG = {
    "host": os.getenv("WORKFLOW_DB_HOST", "localhost"),
    "port": os.getenv("WORKFLOW_DB_PORT", "5432"),
    "dbname": os.getenv("WORKFLOW_DB_NAME", "workflow_automation"),
    "user": os.getenv("WORKFLOW_DB_USER", "postgres"),
    "password": os.getenv("WORKFLOW_DB_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def failing_stage(*args, **kwargs):
    """
    Controlled failure used only for QA.
    """
    raise RuntimeError("CONTROLLED QA FAILURE TEST")


def get_latest_run():

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    run_id,
                    workflow_name,
                    status,
                    error_message,
                    started_at,
                    completed_at
                FROM analytics.workflow_runs
                ORDER BY started_at DESC
                LIMIT 1;
                """
            )

            return cursor.fetchone()

    finally:
        connection.close()


def main():

    original_run_stage = workflow_runner.run_stage

    print("=" * 70)
    print("WORKFLOW AUTOMATION HUB")
    print("FAILURE-HANDLING QA TEST")
    print("=" * 70)

    try:

        print("\n1. Injecting controlled workflow failure...")

        workflow_runner.run_stage = failing_stage

        print("   ✅ Controlled failure injected.")

        print("\n2. Running real workflow orchestrator...")

        try:
            workflow_runner.main()

        except RuntimeError as error:

            # This is EXPECTED.
            # workflow_runner.main() re-raises the controlled failure
            # after its own failure-handling logic executes.

            if str(error) == "CONTROLLED QA FAILURE TEST":

                print(
                    "   ✅ Expected controlled exception received."
                )

            else:

                print(
                    f"   ❌ Unexpected RuntimeError: {error}"
                )

                return False

        print("\n3. Checking workflow audit record...")

        latest_run = get_latest_run()

        if latest_run is None:

            print("   ❌ No workflow audit record found.")
            return False

        run_id = latest_run[0]
        workflow_name = latest_run[1]
        status = latest_run[2]
        error_message = latest_run[3]

        print(f"   Run ID:        {run_id}")
        print(f"   Workflow:      {workflow_name}")
        print(f"   Status:        {status}")
        print(f"   Error Message: {error_message}")

        if status != "FAILED":

            print(
                "\n   ❌ Expected workflow status: FAILED"
            )

            return False

        if error_message is None:

            print(
                "\n   ❌ Expected error_message to be populated"
            )

            return False

        if "CONTROLLED QA FAILURE TEST" not in error_message:

            print(
                "\n   ❌ Expected controlled error was not recorded"
            )

            return False

        print(
            "\n   ✅ Workflow correctly recorded FAILED status."
        )

        print(
            "   ✅ Workflow correctly recorded the error message."
        )

        return True

    finally:

        workflow_runner.run_stage = original_run_stage

        print("\n4. Restoring workflow code...")
        print("   ✅ Original workflow stage restored.")


if __name__ == "__main__":

    passed = main()

    print("\n" + "=" * 70)

    if passed:
        print("✅ FAILURE-HANDLING QA TEST: PASS")
    else:
        print("❌ FAILURE-HANDLING QA TEST: FAIL")

    print("=" * 70)