from pydantic import BaseModel, Field


class IdentityResponse(BaseModel):
    employee_id: str = Field(..., description="Employee ID")
    username: str
    display_name: str | None = None
    email: str | None = None
    groups: list[str] = []