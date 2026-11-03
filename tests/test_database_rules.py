
import sqlite3

from database.connection import get_connection


def run_database_tests():

    connection = get_connection()

    try:
        user = connection.execute(
            "SELECT user_id FROM app_users WHERE username = ?",
            ("dev_admin",)
        ).fetchone()

        user_id = user[0]

        print("\nIFTM EMS DATABASE RULES TEST")
        print("=" * 45)

        # TEST 1: Shared mobile number
        connection.execute(
            """
            INSERT INTO students (
                student_name, father_name, mobile_number,
                address, city, created_by_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Amit Sharma", "Rajesh Sharma", "9876543210",
                "Civil Lines", "Moradabad", user_id
            )
        )

        shared_mobile_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM students
            WHERE mobile_number = ?
            """,
            ("9876543210",)
        ).fetchone()[0]

        assert shared_mobile_count == 2
        print("PASS: Two students can share a mobile number.")

        # TEST 2: Existing student with ERP ID and roll number
        connection.execute(
            """
            INSERT INTO students (
                student_name, father_name, mobile_number,
                address, city, erp_student_unique_id,
                roll_number, student_type, created_by_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Neha Verma", "Suresh Verma", "9123456780",
                "Moradabad", "Moradabad", "ERP-TEST-001",
                "CSE-2025-015", "EXISTING_STUDENT", user_id
            )
        )

        existing = connection.execute(
            """
            SELECT student_type, roll_number
            FROM students
            WHERE erp_student_unique_id = ?
            """,
            ("ERP-TEST-001",)
        ).fetchone()

        assert existing == ("EXISTING_STUDENT", "CSE-2025-015")
        print("PASS: Existing student and roll number saved.")

        # TEST 3: Duplicate ERP Student Unique ID
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO students (
                        student_name, father_name, mobile_number,
                        address, city, erp_student_unique_id,
                        created_by_user_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Duplicate Student", "Test Father",
                        "9000000000", "Test Address", "Moradabad",
                        "ERP-TEST-001", user_id
                    )
                )

            raise AssertionError("Duplicate ERP ID was accepted.")

        except sqlite3.IntegrityError:
            print("PASS: Duplicate ERP Student Unique ID rejected.")

        # TEST 4: Invalid student foreign key
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO enquiries (
                        student_id, source_id, entered_by_user_id
                    )
                    VALUES (?, ?, ?)
                    """,
                    (999999, 1, user_id)
                )

            raise AssertionError("Invalid student reference was accepted.")

        except sqlite3.IntegrityError:
            print("PASS: Invalid student reference rejected.")

        # TEST 5: Master data counts
        source_count = connection.execute(
            "SELECT COUNT(*) FROM enquiry_sources"
        ).fetchone()[0]

        programme_count = connection.execute(
            "SELECT COUNT(*) FROM programmes"
        ).fetchone()[0]

        assert source_count == 10
        assert programme_count == 7

        print("PASS: Master data remains unchanged.")

        print("\nALL DATABASE RULES TESTS PASSED.")

    finally:
        connection.close()


if __name__ == "__main__":
    run_database_tests()
