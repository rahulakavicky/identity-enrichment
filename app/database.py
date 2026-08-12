import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# Database configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "identity.db"


# ============================================================
# Connection
# ============================================================

def get_connection():
    """
    Create a connection to the SQLite database.
    """

    conn = sqlite3.connect(DB_PATH)

    # Return rows that can be accessed by column name.
    conn.row_factory = sqlite3.Row

    # Enable foreign-key enforcement.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# Database initialization
# ============================================================
def initialize_database():
    """
    Create the identities table if it doesn't exist.

    Also migrate existing databases by adding the `active`
    column when required.
    """

    conn = get_connection()

    try:
        conn.execute(

            """
            CREATE TABLE IF NOT EXISTS sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                started_at TEXT NOT NULL,
                completed_at TEXT,

                status TEXT NOT NULL,

                discovered INTEGER NOT NULL DEFAULT 0,
                created INTEGER NOT NULL DEFAULT 0,
                updated INTEGER NOT NULL DEFAULT 0,
                unchanged INTEGER NOT NULL DEFAULT 0,
                inactive INTEGER NOT NULL DEFAULT 0,
                errors INTEGER NOT NULL DEFAULT 0,

                error_message TEXT
            )
            """
        )

        # ----------------------------------------------------
        # Check whether active column already exists
        # ----------------------------------------------------

        columns = conn.execute(
            "PRAGMA table_info(identities)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "active" not in column_names:

            conn.execute(
                """
                ALTER TABLE identities
                ADD COLUMN active INTEGER
                NOT NULL DEFAULT 1
                """
            )

        conn.commit()

    finally:
        conn.close()
# ============================================================
# Identity retrieval
# ============================================================

def get_identity(employee_id: str):
    """
    Retrieve one identity using employee_id.
    """

    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            SELECT
                employee_id,
                username,
                display_name,
                email,
                distinguished_name,
                groups,
                active,
                last_synced_at,
                created_at,
                updated_at
            FROM identities
            WHERE employee_id = ?
            """,
            (employee_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()


# ============================================================
# Identity count
# ============================================================

def count_identities():
    """
    Return the number of identities currently stored.
    """

    conn = get_connection()

    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM identities"
        )

        return cursor.fetchone()[0]

    finally:
        conn.close()


# ============================================================
# Identity upsert
# ============================================================

def upsert_identity(identity: dict):
    """
    Insert a new identity or update an existing identity.

    Returns:

        "created"
        "updated"
        "unchanged"
    """

    employee_id = identity["employee_id"]

    existing = get_identity(employee_id)

    now = datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------------
    # New identity
    # --------------------------------------------------------

    if existing is None:

        conn = get_connection()

        try:
            conn.execute(
                """
                INSERT INTO identities (
                    employee_id,
                    username,
                    display_name,
                    email,
                    distinguished_name,
                    groups,
                    active,
                    last_synced_at,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity["employee_id"],
                    identity["username"],
                    identity["display_name"],
                    identity["email"],
                    identity["distinguished_name"],
                    _serialize_groups(identity["groups"]),
                    1,
                    now,
                    now,
                    now,
                ),
            )

            conn.commit()

        finally:
            conn.close()

        return "created"

    # --------------------------------------------------------
    # Compare existing identity
    # --------------------------------------------------------

    existing_groups = existing["groups"] or "[]"

    new_groups = _serialize_groups(
        identity["groups"]
    )

    changed = (
        existing["username"] != identity["username"]
        or existing["display_name"] != identity["display_name"]
        or existing["email"] != identity["email"]
        or existing["distinguished_name"]
        != identity["distinguished_name"]
        or existing_groups != new_groups
        or existing.get("active", 1) != 1
    )

    # --------------------------------------------------------
    # Nothing changed
    # --------------------------------------------------------

    if not changed:

        conn = get_connection()

        try:
            conn.execute(
                """
                UPDATE identities
                SET last_synced_at = ?
                WHERE employee_id = ?
                """,
                (
                    now,
                    employee_id,
                ),
            )

            conn.commit()

        finally:
            conn.close()

        return "unchanged"

    # --------------------------------------------------------
    # Update existing identity
    # --------------------------------------------------------

    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE identities
            SET
                username = ?,
                display_name = ?,
                email = ?,
                distinguished_name = ?,
                groups = ?,
                active = 1,
                last_synced_at = ?,
                updated_at = ?
            WHERE employee_id = ?
            """,
            (
                identity["username"],
                identity["display_name"],
                identity["email"],
                identity["distinguished_name"],
                new_groups,
                now,
                now,
                employee_id,
            ),
        )

        conn.commit()

    finally:
        conn.close()

    return "updated"
def mark_missing_identities_inactive(
    synced_employee_ids: set[str],
):
    """
    Mark identities as inactive when they are no longer
    present in the latest Active Directory synchronization.

    Returns the number of identities marked inactive.
    """

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT employee_id
            FROM identities
            WHERE active = 1
            """
        ).fetchall()

        inactive_count = 0

        for row in rows:

            employee_id = row["employee_id"]

            if employee_id not in synced_employee_ids:

                conn.execute(
                    """
                    UPDATE identities
                    SET
                        active = 0,
                        updated_at = ?
                    WHERE employee_id = ?
                    """,
                    (
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                        employee_id,
                    ),
                )

                inactive_count += 1

        conn.commit()

        return inactive_count

    finally:
        conn.close()
# ============================================================
# Group serialization
# ============================================================

def _serialize_groups(groups):
    """
    Store LDAP group membership as JSON text.
    """

    import json

    if not groups:
        return "[]"

    return json.dumps(
        groups,
        sort_keys=True,
    )

def create_sync_run():
    """
    Create a new synchronization run.

    Returns the sync run ID.
    """

    conn = get_connection()

    started_at = datetime.now(timezone.utc).isoformat()

    try:
        cursor = conn.execute(
            """
            INSERT INTO sync_runs (
                started_at,
                status
            )
            VALUES (?, ?)
            """,
            (
                started_at,
                "RUNNING",
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def complete_sync_run(
    sync_id: int,
    status: str,
    discovered: int,
    created: int,
    updated: int,
    unchanged: int,
    inactive: int,
    errors: int,
    error_message: str | None = None,
):
    """
    Mark a synchronization run as completed.
    """

    conn = get_connection()

    completed_at = datetime.now(timezone.utc).isoformat()

    try:
        conn.execute(
            """
            UPDATE sync_runs
            SET
                completed_at = ?,
                status = ?,
                discovered = ?,
                created = ?,
                updated = ?,
                unchanged = ?,
                inactive = ?,
                errors = ?,
                error_message = ?
            WHERE id = ?
            """,
            (
                completed_at,
                status,
                discovered,
                created,
                updated,
                unchanged,
                inactive,
                errors,
                error_message,
                sync_id,
            ),
        )

        conn.commit()

    finally:
        conn.close()


def get_latest_sync_run():
    """
    Return the most recent synchronization run.
    """

    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            SELECT
                id,
                started_at,
                completed_at,
                status,
                discovered,
                created,
                updated,
                unchanged,
                inactive,
                errors,
                error_message
            FROM sync_runs
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()