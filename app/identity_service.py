from app.database import get_identity


def get_identity_by_employee_id(
    employee_id: str,
    include_inactive: bool = False,
):
    """
    Retrieve an identity using employee ID.

    Converts database-specific representations
    into API-friendly Python objects.
    """

    # --------------------------------------------------------
    # Validate employee ID
    # --------------------------------------------------------

    if not employee_id:
        return None

    employee_id = employee_id.strip()

    if not employee_id:
        return None

    # --------------------------------------------------------
    # Retrieve identity
    # --------------------------------------------------------

    identity = get_identity(employee_id)

    if identity is None:
        return None

    # --------------------------------------------------------
    # Check active status
    # --------------------------------------------------------

    if identity.get("active") != 1:

        if not include_inactive:
            return None

    # --------------------------------------------------------
    # Normalize groups
    # --------------------------------------------------------

    groups = identity.get("groups")

    if groups is None:
        identity["groups"] = []

    elif isinstance(groups, str):

        if groups.strip() == "[]":
            identity["groups"] = []

        else:
            identity["groups"] = [
                group.strip()
                for group in groups.split(",")
                if group.strip()
            ]

    elif not isinstance(groups, list):

        identity["groups"] = []

    return identity