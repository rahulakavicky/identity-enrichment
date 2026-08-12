import logging
import os
import sys

from logging.handlers import RotatingFileHandler


# ============================================================
# Configuration
# ============================================================

LOG_DIRECTORY = "logs"
LOG_FILE = os.path.join(
    LOG_DIRECTORY,
    "audit.log",
)


# ============================================================
# Create log directory
# ============================================================

os.makedirs(
    LOG_DIRECTORY,
    exist_ok=True,
)


# ============================================================
# Audit Logger
# ============================================================

audit_logger = logging.getLogger(
    "identity_audit"
)

audit_logger.setLevel(
    logging.INFO
)

audit_logger.propagate = False


# ============================================================
# Log Format
# ============================================================

formatter = logging.Formatter(
    "%(asctime)s "
    "level=%(levelname)s "
    "logger=%(name)s "
    "message=%(message)s"
)


# ============================================================
# Console Handler
# ============================================================

console_handler = logging.StreamHandler(
    sys.stdout
)

console_handler.setLevel(
    logging.INFO
)

console_handler.setFormatter(
    formatter
)


# ============================================================
# File Handler
# ============================================================

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
)

file_handler.setLevel(
    logging.INFO
)

file_handler.setFormatter(
    formatter
)


# ============================================================
# Register Handlers
# ============================================================

if not audit_logger.handlers:

    audit_logger.addHandler(
        console_handler
    )

    audit_logger.addHandler(
        file_handler
    )


# ============================================================
# Audit Function
# ============================================================

def audit_event(
    *,
    request_id: str,
    client_ip: str,
    method: str,
    path: str,
    employee_id: str | None,
    status_code: int,
    duration_ms: float,
):
    """
    Write a structured audit event.

    Never log:
        - API keys
        - passwords
        - LDAP credentials
        - private keys
        - TLS secrets
    """

    audit_logger.info(
        "request_id=%s "
        "client_ip=%s "
        "method=%s "
        "path=%s "
        "employee_id=%s "
        "status_code=%s "
        "duration_ms=%.2f",
        request_id,
        client_ip,
        method,
        path,
        employee_id,
        status_code,
        duration_ms,
    )