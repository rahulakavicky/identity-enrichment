import time
import uuid 

from fastapi import FastAPI, HTTPException, Security, Request 

from app.audit import audit_event 

from app.identity_service import (
    get_identity_by_employee_id,
)

from app.models import IdentityResponse
from app.security import get_api_key


app = FastAPI(
    title="Identity Enrichment API",
    version="1.0.0",
    description="Identity enrichment service for security telemetry",
)

@app.middleware("http")
async def audit_middleware(request: Request, call_next):

    # --------------------------------------------------------
    # Generate unique request ID
    # --------------------------------------------------------

    request_id = str(uuid.uuid4())

    # --------------------------------------------------------
    # Record start time
    # --------------------------------------------------------

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Client information
    # --------------------------------------------------------

    client_ip = "unknown"

    if request.client:
        client_ip = request.client.host

    # --------------------------------------------------------
    # Execute request
    # --------------------------------------------------------

    response = await call_next(request)

    # --------------------------------------------------------
    # Calculate duration
    # --------------------------------------------------------

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # --------------------------------------------------------
    # Extract employee ID
    # --------------------------------------------------------

    employee_id = request.path_params.get(
        "employee_id"
    )

    # --------------------------------------------------------
    # Write audit event
    # --------------------------------------------------------

    audit_event(
        request_id=request_id,
        client_ip=client_ip,
        method=request.method,
        path=request.url.path,
        employee_id=employee_id,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    # --------------------------------------------------------
    # Return request ID to caller
    # --------------------------------------------------------

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response



# ============================================================
# Health
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ============================================================
# Identity Lookup
# ============================================================

@app.get(
    "/api/v1/identity/{employee_id}",
    response_model=IdentityResponse,
)
def identity_lookup(
    employee_id: str,
    api_key: str = Security(get_api_key),
):

    identity = get_identity_by_employee_id(
        employee_id
    )

    if identity is None:

        raise HTTPException(
            status_code=404,
            detail="Identity not found",
        )

    return identity