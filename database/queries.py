
from database.connection import get_connection


def get_dashboard_stats():

    connection = get_connection()

    try:
        total_enquiries = connection.execute("""
            SELECT COUNT(*) FROM enquiries
        """).fetchone()[0]

        total_students = connection.execute("""
            SELECT COUNT(*) FROM students
        """).fetchone()[0]

        new_enquiries = connection.execute("""
            SELECT COUNT(*)
            FROM enquiries
            WHERE enquiry_status = 'NEW'
        """).fetchone()[0]

        existing_students = connection.execute("""
            SELECT COUNT(*)
            FROM students
            WHERE student_type = 'EXISTING_STUDENT'
        """).fetchone()[0]

        return (
            total_enquiries,
            total_students,
            new_enquiries,
            existing_students
        )

    finally:
        connection.close()


def get_dropdown_data():

    connection = get_connection()

    try:
        sources = connection.execute("""
            SELECT source_id, source_name
            FROM enquiry_sources
            WHERE is_active = 1
            ORDER BY source_name
        """).fetchall()

        programmes = connection.execute("""
            SELECT programme_id, programme_name
            FROM programmes
            WHERE is_active = 1
            ORDER BY programme_name
        """).fetchall()

        return sources, programmes

    finally:
        connection.close()


def find_existing_mobile(mobile_number):

    connection = get_connection()

    try:
        result = connection.execute("""
            SELECT student_id, student_name, father_name
            FROM students
            WHERE mobile_number = ?
        """, (mobile_number,)).fetchall()

        return result

    finally:
        connection.close()


def search_students(search_text):

    connection = get_connection()

    try:
        search_pattern = f"%{search_text.strip()}%"

        results = connection.execute("""
            SELECT
                student_id,
                student_name,
                father_name,
                mobile_number,
                city,
                student_type,
                erp_student_unique_id,
                roll_number
            FROM students
            WHERE student_name LIKE ?
               OR mobile_number LIKE ?
               OR erp_student_unique_id LIKE ?
               OR roll_number LIKE ?
            ORDER BY student_name
        """, (
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern
        )).fetchall()

        return results

    finally:
        connection.close()


def get_student_enquiry_history(student_id):

    connection = get_connection()

    try:
        results = connection.execute("""
            SELECT
                e.enquiry_id,
                es.source_name,
                p.programme_name,
                e.enquiry_status,
                e.enquiry_date
            FROM enquiries e
            JOIN enquiry_sources es
                ON e.source_id = es.source_id
            LEFT JOIN programmes p
                ON e.programme_id = p.programme_id
            WHERE e.student_id = ?
            ORDER BY e.enquiry_date DESC, e.enquiry_id DESC
        """, (student_id,)).fetchall()

        return results

    finally:
        connection.close()

def update_enquiry_status(enquiry_id, new_status):

    allowed_statuses = [
        "NEW",
        "CONTACTED",
        "INTERESTED",
        "NOT_INTERESTED",
        "FOLLOW_UP_REQUIRED",
        "CLOSED"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid enquiry status.")

    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        record = cursor.execute("""
            SELECT enquiry_status
            FROM enquiries
            WHERE enquiry_id = ?
        """, (enquiry_id,)).fetchone()

        if record is None:
            raise ValueError("Enquiry record not found.")

        old_status = record[0]

        if old_status == new_status:
            return False

        cursor.execute("""
            UPDATE enquiries
            SET enquiry_status = ?
            WHERE enquiry_id = ?
        """, (new_status, enquiry_id))

        cursor.execute("""
            INSERT INTO audit_logs (
                user_id,
                entity_type,
                entity_id,
                action,
                details
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            current_user_id,
            "ENQUIRY",
            enquiry_id,
            "STATUS_UPDATED",
            f"Status changed from {old_status} to {new_status}"
        ))

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_call_activity(
    enquiry_id,
    call_outcome,
    remarks,
    next_follow_up_date
):

    allowed_outcomes = [
        "ANSWERED",
        "NO_ANSWER",
        "BUSY",
        "SWITCHED_OFF",
        "INVALID_NUMBER",
        "CALL_BACK_REQUESTED",
        "OTHER"
    ]

    if call_outcome not in allowed_outcomes:
        raise ValueError("Invalid call outcome.")

    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        enquiry = cursor.execute("""
            SELECT enquiry_id
            FROM enquiries
            WHERE enquiry_id = ?
        """, (enquiry_id,)).fetchone()

        if enquiry is None:
            raise ValueError("Enquiry record not found.")

        cursor.execute("""
            INSERT INTO calling_activities (
                enquiry_id,
                call_outcome,
                remarks,
                next_follow_up_date,
                recorded_by_user_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            enquiry_id,
            call_outcome,
            remarks or None,
            next_follow_up_date or None,
            current_user_id
        ))

        call_activity_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO audit_logs (
                user_id,
                entity_type,
                entity_id,
                action,
                details
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            current_user_id,
            "CALLING_ACTIVITY",
            call_activity_id,
            "CALL_RECORDED",
            f"Call recorded for Enquiry #{enquiry_id}. "
            f"Outcome: {call_outcome}"
        ))

        connection.commit()

        return call_activity_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_enquiries_for_calling():

    connection = get_connection()

    try:
        results = connection.execute("""
            SELECT
                e.enquiry_id,
                s.student_name,
                s.mobile_number,
                p.programme_name,
                e.enquiry_status
            FROM enquiries e
            JOIN students s
                ON e.student_id = s.student_id
            LEFT JOIN programmes p
                ON e.programme_id = p.programme_id
            ORDER BY e.enquiry_id DESC
        """).fetchall()

        return results

    finally:
        connection.close()


def get_calling_history(enquiry_id):

    connection = get_connection()

    try:
        results = connection.execute("""
            SELECT
                ca.call_activity_id,
                ca.call_datetime,
                ca.call_outcome,
                ca.remarks,
                ca.next_follow_up_date,
                u.full_name
            FROM calling_activities ca
            JOIN app_users u
                ON ca.recorded_by_user_id = u.user_id
            WHERE ca.enquiry_id = ?
            ORDER BY ca.call_datetime DESC,
                     ca.call_activity_id DESC
        """, (enquiry_id,)).fetchall()

        return results

    finally:
        connection.close()


def get_follow_up_tasks():

    connection = get_connection()

    try:
        results = connection.execute("""
            SELECT
                ca.call_activity_id,
                e.enquiry_id,
                s.student_name,
                s.mobile_number,
                p.programme_name,
                ca.call_outcome,
                ca.remarks,
                ca.next_follow_up_date,
                u.full_name
            FROM calling_activities ca
            JOIN enquiries e
                ON ca.enquiry_id = e.enquiry_id
            JOIN students s
                ON e.student_id = s.student_id
            LEFT JOIN programmes p
                ON e.programme_id = p.programme_id
            JOIN app_users u
                ON ca.recorded_by_user_id = u.user_id
            WHERE ca.next_follow_up_date IS NOT NULL
            ORDER BY ca.next_follow_up_date ASC
        """).fetchall()

        return results

    finally:
        connection.close()

def save_enquiry(
    student_name,
    father_name,
    mobile_number,
    address,
    city,
    source_id,
    programme_id,
    referrer_details
):

    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO students (
                student_name,
                father_name,
                mobile_number,
                address,
                city,
                created_by_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_name,
            father_name,
            mobile_number,
            address,
            city,
            current_user_id
        ))

        student_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO enquiries (
                student_id,
                source_id,
                programme_id,
                entered_by_user_id,
                referrer_details
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_id,
            source_id,
            programme_id,
            current_user_id,
            referrer_details or None
        ))

        enquiry_id = cursor.lastrowid

        connection.commit()

        return student_id, enquiry_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
