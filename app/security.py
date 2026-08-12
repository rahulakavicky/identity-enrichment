import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


API_KEY_HEADER = "X-API-Key"

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
)


def get_api_key(
    api_key: str | None = Security(api_key_header),
):
    """
    Validate the API key supplied by the caller.
    """

    expected_api_key = os.getenv("IDENTITY_API_KEY")

    if not expected_api_key:
        raise RuntimeError(
            "IDENTITY_API_KEY environment variable is not configured"
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key