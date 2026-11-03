
from database.connection import get_connection


def create_test_records():

    connection = get_connection()

    try:
        with connection:

            # ----------------------------------
            # STEP 1: GET DEVELOPMENT USER
            # ----------------------------------

            user = connection.execute(
                """
                SELECT user_id
                FROM app_users
                WHERE username = ?
                """,
                ("dev_admin",)
            ).fetchone()

            if user is None:
                raise ValueError("Development user not found.")

            user_id = user[0]

            # ----------------------------------
            # STEP 2: FIND OR CREATE STUDENT
            # ----------------------------------

            student = connection.execute(
                """
                SELECT student_id
                FROM students
                WHERE student_name = ?
                  AND father_name = ?
                  AND mobile_number = ?
                """,
                ("Rahul Sharma", "Rajesh Sharma", "9876543210")
            ).fetchone()

            if student is None:

                cursor = connection.execute(
                    """
                    INSERT INTO students (
                        student_name,
                        father_name,
                        mobile_number,
                        address,
                        city,
                        student_type,
                        created_by_user_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Rahul Sharma",
                        "Rajesh Sharma",
                        "9876543210",
                        "Civil Lines, Moradabad",
                        "Moradabad",
                        "NEW_PROSPECT",
                        user_id
                    )
                )

                student_id = cursor.lastrowid

            else:
                student_id = student[0]

            student_display_id = f"STU-{student_id:06d}"

            # ----------------------------------
            # STEP 3: GET ENQUIRY SOURCES
            # ----------------------------------

            website = connection.execute(
                """
                SELECT source_id
                FROM enquiry_sources
                WHERE source_name = ?
                """,
                ("Website",)
            ).fetchone()

            faculty_referral = connection.execute(
                """
                SELECT source_id
                FROM enquiry_sources
                WHERE source_name = ?
                """,
                ("Faculty Referral",)
            ).fetchone()

            if website is None or faculty_referral is None:
                raise ValueError("Required enquiry source not found.")

            # ----------------------------------
            # STEP 4: GET PROGRAMME
            # ----------------------------------

            programme = connection.execute(
                """
                SELECT programme_id
                FROM programmes
                WHERE programme_name = ?
                  AND department_name = ?
                """,
                (
                    "B.Tech CSE",
                    "Department of Computer Science and Engineering"
                )
            ).fetchone()

            if programme is None:
                raise ValueError("B.Tech CSE programme not found.")

            programme_id = programme[0]

            # ----------------------------------
            # STEP 5: CREATE TWO ENQUIRIES
            # ----------------------------------

            enquiry_data = [
                (website[0], "Website enquiry"),
                (faculty_referral[0], "Faculty referral enquiry")
            ]

            enquiry_ids = []

            for source_id, remarks in enquiry_data:

                existing = connection.execute(
                    """
                    SELECT enquiry_id
                    FROM enquiries
                    WHERE student_id = ?
                      AND source_id = ?
                      AND programme_id = ?
                      AND referrer_details = ?
                    """,
                    (
                        student_id,
                        source_id,
                        programme_id,
                        remarks
                    )
                ).fetchone()

                if existing is None:

                    cursor = connection.execute(
                        """
                        INSERT INTO enquiries (
                            student_id,
                            source_id,
                            programme_id,
                            entered_by_user_id,
                            referrer_details
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            student_id,
                            source_id,
                            programme_id,
                            user_id,
                            remarks
                        )
                    )

                    enquiry_ids.append(cursor.lastrowid)

                else:
                    enquiry_ids.append(existing[0])

            # ----------------------------------
            # STEP 6: DISPLAY RESULTS
            # ----------------------------------

            print("\nTEST RECORDS CREATED / VERIFIED")
            print("=" * 40)

            print("Student ID:", student_display_id)
            print("Student Name: Rahul Sharma")

            print("\nEnquiries:")

            for enquiry_id in enquiry_ids:
                print(f"ENQ-{enquiry_id:06d}")

            print("\nStudent ID:", student_id)
            print("Total Enquiries:", connection.execute(
                """
                SELECT COUNT(*)
                FROM enquiries
                WHERE student_id = ?
                """,
                (student_id,)
            ).fetchone()[0])

            print("\nTransaction completed successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    create_test_records()
