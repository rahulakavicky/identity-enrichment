import time
from collections import defaultdict
from threading import Lock


# ============================================================
# Configuration
# ============================================================

MAX_REQUESTS = 100
WINDOW_SECONDS = 60


# ============================================================
# Request Tracking
# ============================================================

request_history = defaultdict(list)

lock = Lock()


# ============================================================
# Rate Limit Check
# ============================================================

def is_rate_limited(client_ip: str) -> bool:
    """
    Return True when the client has exceeded
    the configured request limit.
    """

    now = time.time()

    with lock:

        requests = request_history[client_ip]

        # ----------------------------------------------------
        # Remove requests outside the current window
        # ----------------------------------------------------

        requests[:] = [
            timestamp
            for timestamp in requests
            if now - timestamp < WINDOW_SECONDS
        ]

        # ----------------------------------------------------
        # Check limit
        # ----------------------------------------------------

        if len(requests) >= MAX_REQUESTS:
            return True

        # ----------------------------------------------------
        # Record current request
        # ----------------------------------------------------

        requests.append(now)

        return False