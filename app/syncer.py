from app.ldap_client import search_employees
from app.database import (
    initialize_database,
    upsert_identity,
    mark_missing_identities_inactive,
    create_sync_run,
    complete_sync_run,
)
MINIMUM_EXPECTED_IDENTITIES = 1


# ============================================================
# Synchronization
# ============================================================

def sync_identities():
    """
    Synchronize identities from Active Directory
    into the local SQLite identity store.
    """

    print("=" * 60)
    print("Identity Synchronization Started")
    print("=" * 60)

    # --------------------------------------------------------
    # Initialize database
    # --------------------------------------------------------

    initialize_database()
    sync_id = create_sync_run()

    print(
        f"Sync Run ID: {sync_id}"
    )
    # --------------------------------------------------------
    # Retrieve identities from AD
    # --------------------------------------------------------

    print("\nConnecting to Active Directory...")

    employees = search_employees()

    if not employees:
        print(
            "\nWARNING: LDAP returned zero identities."
        )

        print(
            "Skipping inactive-user processing."
        )

        return {
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "inactive": 0,
            "errors": 1,
        }


    print(
        f"Employees discovered in AD: "
        f"{len(employees)}"
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    created = 0
    updated = 0
    unchanged = 0
    errors = 0

    # --------------------------------------------------------
    # Process each identity
    # --------------------------------------------------------

    for employee in employees:

        employee_id = employee.get(
            "employee_id"
        )

        if not employee_id:
            print(
                "Skipping identity without employeeID"
            )

            errors += 1
            continue

        try:

            result = upsert_identity(
                employee
            )

            if result == "created":
                created += 1

            elif result == "updated":
                updated += 1

            elif result == "unchanged":
                unchanged += 1

            print(
                f"[{result.upper():9}] "
                f"{employee_id} "
                f"{employee['username']}"
            )

        except Exception as exc:

            errors += 1

            print(
                f"[ERROR] "
                f"{employee_id} "
                f"{employee.get('username')} "
                f"-> {exc}"
            )

    # --------------------------------------------------------
    # Mark identities missing from AD as inactive
    # --------------------------------------------------------

    synced_employee_ids = {
        employee["employee_id"]
        for employee in employees
        if employee.get("employee_id")
    }

    inactive = mark_missing_identities_inactive(
        synced_employee_ids
    )

    print(
        f"Marked inactive: {inactive}"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("Identity Synchronization Completed")
    print("=" * 60)

    print(
        f"AD identities : {len(employees)}"
    )

    print(
        f"Created       : {created}"
    )

    print(
        f"Updated       : {updated}"
    )

    print(
        f"Unchanged     : {unchanged}"
    )

    print(
        f"Inactive      : {inactive}"
    )

    print(
        f"Errors        : {errors}"
    )

    print("=" * 60)

    complete_sync_run(
        sync_id=sync_id,
        status="SUCCESS",
        discovered=len(employees),
        created=created,
        updated=updated,
        unchanged=unchanged,
        inactive=inactive,
        errors=errors,
    )

    return {
        "discovered": len(employees),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "inactive": inactive,
        "errors": errors,
    }

# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    sync_identities()

