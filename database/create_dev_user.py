
import os
import getpass
import hashlib

from database.connection import get_connection


def create_development_user():

    username = "dev_admin"
    full_name = "Development Administrator"

    connection = get_connection()

    try:
        # Check whether the development user already exists
        existing_user = connection.execute(
            "SELECT user_id FROM app_users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            print("Development user already exists.")
            print("User ID:", existing_user[0])
            print("No changes made.")
            return

        # Ask for password securely
        password = getpass.getpass("Enter development password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if not password:
            raise ValueError("Password cannot be empty.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        # Generate a random salt
        salt = os.urandom(16)

        # Generate PBKDF2 password hash
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600000
        )

        stored_hash = (
            f"pbkdf2_sha256$600000$"
            f"{salt.hex()}${password_hash.hex()}"
        )

        with connection:
            cursor = connection.execute(
                """
                INSERT INTO app_users (
                    full_name,
                    username,
                    password_hash,
                    role
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    full_name,
                    username,
                    stored_hash,
                    "SYSTEM_ADMIN"
                )
            )

        print("Development user created successfully.")
        print("User ID:", cursor.lastrowid)
        print("Username:", username)
        print("Role: SYSTEM_ADMIN")

    finally:
        connection.close()


if __name__ == "__main__":
    create_development_user()
