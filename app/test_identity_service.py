from app.identity_service import get_identity_by_employee_id


def main():

    print("=" * 60)
    print("Identity Service Test")
    print("=" * 60)

    # --------------------------------------------------------
    # Existing employee
    # --------------------------------------------------------

    result = get_identity_by_employee_id("2")

    print("\nEmployee 2:")
    print(result)

    # --------------------------------------------------------
    # Another existing employee
    # --------------------------------------------------------

    result = get_identity_by_employee_id("3")

    print("\nEmployee 3:")
    print(result)

    # --------------------------------------------------------
    # Non-existing employee
    # --------------------------------------------------------

    result = get_identity_by_employee_id("999")

    print("\nEmployee 999:")
    print(result)


if __name__ == "__main__":
    main()