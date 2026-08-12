from app.database import (
    initialize_database,
    count_identities,
    DB_PATH,
)


def main():

    print("Initializing database...")

    initialize_database()

    print(f"Database: {DB_PATH}")
    print(f"Identities: {count_identities()}")


if __name__ == "__main__":
    main()