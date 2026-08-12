import os
import ssl

from dotenv import load_dotenv
from ldap3 import Server, Connection, Tls, ALL, SUBTREE


load_dotenv()


# ============================================================
# Configuration
# ============================================================

AD_HOST = os.getenv("AD_HOST", "dc01.corp.example")
AD_PORT = int(os.getenv("AD_PORT", "636"))

AD_USER = os.getenv("AD_USER")
AD_PASSWORD = os.getenv("AD_PASSWORD")

AD_BASE_DN = os.getenv(
    "AD_BASE_DN",
    "DC=corp,DC=example",
)

AD_CA_CERT = os.getenv(
    "AD_CA_CERT",
    "/etc/ssl/certs/corp-ad-ca.pem",
)


# ============================================================
# TLS
# ============================================================

tls_config = Tls(
    ca_certs_file=AD_CA_CERT,
    validate=ssl.CERT_REQUIRED,
    version=ssl.PROTOCOL_TLS_CLIENT,
)


# ============================================================
# LDAP connection
# ============================================================

def _create_connection():
    """
    Create and authenticate an LDAPS connection to Active Directory.
    """

    if not AD_USER:
        raise RuntimeError("AD_USER is not configured")

    if not AD_PASSWORD:
        raise RuntimeError("AD_PASSWORD is not configured")

    server = Server(
        AD_HOST,
        port=AD_PORT,
        use_ssl=True,
        tls=tls_config,
        get_info=ALL,
        connect_timeout=5,
    )

    return Connection(
        server,
        user=AD_USER,
        password=AD_PASSWORD,
        auto_bind=True,
        receive_timeout=10,
        raise_exceptions=True,
    )


# ============================================================
# Single employee lookup
# ============================================================

def lookup_employee(employee_id: str) -> list[dict]:
    """
    Look up one employee using employeeID.
    """

    employee_id = str(employee_id).strip()

    if not employee_id:
        raise ValueError("employee_id cannot be empty")

    if not employee_id.isdigit():
        raise ValueError("employee_id must contain only digits")

    conn = None

    try:
        conn = _create_connection()

        search_filter = (
            f"(&(objectClass=user)(employeeID={employee_id}))"
        )

        conn.search(
            search_base=AD_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=[
                "sAMAccountName",
                "employeeID",
                "displayName",
                "mail",
                "distinguishedName",
                "memberOf",
            ],
        )

        return [
            _normalize_entry(entry)
            for entry in conn.entries
        ]

    finally:
        if conn is not None and conn.bound:
            conn.unbind()


# ============================================================
# Bulk employee search
# ============================================================

def search_employees() -> list[dict]:
    """
    Retrieve all AD users that have an employeeID.

    This function is intended for the synchronization process.
    """

    conn = None

    try:
        conn = _create_connection()

        search_filter = (
            "(&(objectClass=user)(employeeID=*))"
        )

        conn.search(
            search_base=AD_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=[
                "sAMAccountName",
                "employeeID",
                "displayName",
                "mail",
                "distinguishedName",
                "memberOf",
            ],
        )

        employees = []

        for entry in conn.entries:
            employee = _normalize_entry(entry)

            # Only synchronize records with a valid employee ID.
            if employee["employee_id"]:
                employees.append(employee)

        return employees

    finally:
        if conn is not None and conn.bound:
            conn.unbind()


# ============================================================
# LDAP normalization
# ============================================================

def _normalize_entry(entry) -> dict:
    """
    Convert an ldap3 Entry into a normal Python dictionary.
    """

    return {
        "username": _get_attribute(
            entry,
            "sAMAccountName",
        ),
        "employee_id": _get_attribute(
            entry,
            "employeeID",
        ),
        "display_name": _get_attribute(
            entry,
            "displayName",
        ),
        "email": _get_attribute(
            entry,
            "mail",
        ),
        "distinguished_name": _get_attribute(
            entry,
            "distinguishedName",
        ),
        "groups": _get_attribute_list(
            entry,
            "memberOf",
        ),
    }


# ============================================================
# Attribute helpers
# ============================================================

def _get_attribute(entry, attribute_name: str):
    """
    Return a single LDAP attribute as a string.
    """

    try:
        value = entry[attribute_name].value
    except (KeyError, TypeError):
        return None

    if value is None:
        return None

    if isinstance(value, list):
        if not value:
            return None

        return str(value[0])

    return str(value)


def _get_attribute_list(
    entry,
    attribute_name: str,
) -> list[str]:
    """
    Return a multi-valued LDAP attribute as a list.
    """

    try:
        values = entry[attribute_name].values
    except (KeyError, TypeError):
        return []

    if not values:
        return []

    return [str(value) for value in values]