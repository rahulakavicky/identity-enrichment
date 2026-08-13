import json
import sqlite3

import pytest

from app import database


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """
    Create an isolated SQLite database for testing.

    The real application database is replaced temporarily
    with a database created inside pytest's temporary directory.
    """

    db_path = tmp_path / "test_identity.db"

    monkeypatch.setattr(database, "DB_PATH", db_path)

    conn = sqlite3.connect(db_path)

    conn.execute(
        """
        CREATE TABLE identities (
            employee_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            display_name TEXT,
            email TEXT,
            distinguished_name TEXT,
            groups TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            last_synced_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()

    return db_path


def test_count_identities_empty_database(test_database):
    """
    A newly created database should contain zero identities.
    """

    assert database.count_identities() == 0


def test_upsert_identity_creates_identity(test_database):
    """
    A new identity should be inserted and reported as 'created'.
    """

    identity = {
        "employee_id": "1001",
        "username": "testuser",
        "display_name": "Test User",
        "email": "testuser@example.com",
        "distinguished_name": "CN=Test User,DC=example,DC=com",
        "groups": ["Employees", "Security"],
    }

    result = database.upsert_identity(identity)

    assert result == "created"
    assert database.count_identities() == 1

    stored_identity = database.get_identity("1001")

    assert stored_identity is not None
    assert stored_identity["employee_id"] == "1001"
    assert stored_identity["username"] == "testuser"
    assert stored_identity["display_name"] == "Test User"
    assert stored_identity["email"] == "testuser@example.com"
    assert json.loads(stored_identity["groups"]) == [
        "Employees",
        "Security",
    ]


def test_upsert_identity_unchanged(test_database):
    """
    Inserting the same identity again without changes
    should return 'unchanged'.
    """

    identity = {
        "employee_id": "1001",
        "username": "testuser",
        "display_name": "Test User",
        "email": "testuser@example.com",
        "distinguished_name": "CN=Test User,DC=example,DC=com",
        "groups": ["Employees"],
    }

    first_result = database.upsert_identity(identity)
    second_result = database.upsert_identity(identity)

    assert first_result == "created"
    assert second_result == "unchanged"
    assert database.count_identities() == 1


def test_upsert_identity_updates_changed_identity(test_database):
    """
    Changing an existing identity should return 'updated'.
    """

    original_identity = {
        "employee_id": "1001",
        "username": "testuser",
        "display_name": "Test User",
        "email": "old@example.com",
        "distinguished_name": "CN=Test User,DC=example,DC=com",
        "groups": ["Employees"],
    }

    updated_identity = {
        "employee_id": "1001",
        "username": "testuser",
        "display_name": "Test User",
        "email": "new@example.com",
        "distinguished_name": "CN=Test User,DC=example,DC=com",
        "groups": ["Employees", "Security"],
    }

    assert database.upsert_identity(original_identity) == "created"

    result = database.upsert_identity(updated_identity)

    assert result == "updated"

    stored_identity = database.get_identity("1001")

    assert stored_identity["email"] == "new@example.com"
    assert json.loads(stored_identity["groups"]) == [
        "Employees",
        "Security",
    ]


def test_get_identity_returns_none_for_unknown_employee(test_database):
    """
    Looking up an employee that does not exist should return None.
    """

    result = database.get_identity("9999")

    assert result is None


def test_mark_missing_identities_inactive(test_database):
    """
    Identities not present in the latest synchronization
    should be marked inactive.
    """

    identity_1 = {
        "employee_id": "1001",
        "username": "user1",
        "display_name": "User One",
        "email": "user1@example.com",
        "distinguished_name": "CN=User One,DC=example,DC=com",
        "groups": [],
    }

    identity_2 = {
        "employee_id": "1002",
        "username": "user2",
        "display_name": "User Two",
        "email": "user2@example.com",
        "distinguished_name": "CN=User Two,DC=example,DC=com",
        "groups": [],
    }

    database.upsert_identity(identity_1)
    database.upsert_identity(identity_2)

    inactive_count = database.mark_missing_identities_inactive(
        {"1001"}
    )

    assert inactive_count == 1

    active_identity = database.get_identity("1001")
    inactive_identity = database.get_identity("1002")

    assert active_identity["active"] == 1
    assert inactive_identity["active"] == 0