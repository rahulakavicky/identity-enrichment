from app.ldap_client import search_employees


def main():
    print("Starting LDAP employee search...\n")

    employees = search_employees()

    print(f"Employees found: {len(employees)}\n")

    for employee in employees:
        print("-" * 60)
        print(f"Username        : {employee['username']}")
        print(f"Employee ID     : {employee['employee_id']}")
        print(f"Display Name    : {employee['display_name']}")
        print(f"Email           : {employee['email']}")
        print(f"Distinguished DN: {employee['distinguished_name']}")
        print(f"Groups          : {employee['groups']}")

    print("\nLDAP employee search completed.")


if __name__ == "__main__":
    main()