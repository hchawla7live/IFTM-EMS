import streamlit as st
import sqlite3
from datetime import date

from database.connection import get_connection


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="IFTM EMS",
    page_icon="🎓",
    layout="wide"
)


# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------
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

    # Development user ID.
    # This will be replaced with the logged-in user's ID
    # when authentication is implemented.
    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Step 1: Get the existing status
        record = cursor.execute("""
            SELECT enquiry_status
            FROM enquiries
            WHERE enquiry_id = ?
        """, (enquiry_id,)).fetchone()

        if record is None:
            raise ValueError("Enquiry record not found.")

        old_status = record[0]

        # Step 2: Avoid unnecessary updates
        if old_status == new_status:
            return False

        # Step 3: Update enquiry status
        cursor.execute("""
            UPDATE enquiries
            SET enquiry_status = ?
            WHERE enquiry_id = ?
        """, (new_status, enquiry_id))

        # Step 4: Record the change in audit logs
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

        # Step 5: Save both operations together
        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
# --------------------------------------------------
# CALLING ACTIVITY DATABASE FUNCTION
# --------------------------------------------------

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

    # Development user ID.
    # Will be replaced with the authenticated user's ID later.
    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Step 1: Verify that the enquiry exists
        enquiry = cursor.execute("""
            SELECT enquiry_id
            FROM enquiries
            WHERE enquiry_id = ?
        """, (enquiry_id,)).fetchone()

        if enquiry is None:
            raise ValueError("Enquiry record not found.")

        # Step 2: Insert a new calling activity
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

        # Step 3: Record the activity in the audit log
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

        # Step 4: Save both records together
        connection.commit()

        return call_activity_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

# --------------------------------------------------
# FETCH ENQUIRIES FOR CALLING
# --------------------------------------------------

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
# --------------------------------------------------
# FETCH CALLING HISTORY
# --------------------------------------------------
# --------------------------------------------------
# FETCH CALLING HISTORY
# --------------------------------------------------

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


# --------------------------------------------------
# FETCH FOLLOW-UP TASKS
# --------------------------------------------------

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

    # Development user ID.
    # We will replace this with the logged-in user's ID
    # when authentication is implemented.
    current_user_id = 1

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Step 1: Create student record
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

        # Step 2: Create linked enquiry record
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

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------

st.title("🎓 IFTM Enquiry Management System")

st.caption(
    "School of Computer Science and Applications | IFTM University"
)

st.divider()


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

st.header("Welcome to IFTM EMS")

st.write(
    "A centralised system for managing student enquiries, "
    "allocations, counselling and admission follow-ups."
)

(
    total_enquiries,
    total_students,
    new_enquiries,
    existing_students
) = get_dashboard_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Enquiries", total_enquiries)

with col2:
    st.metric("Total Students", total_students)

with col3:
    st.metric("New Enquiries", new_enquiries)

with col4:
    st.metric("Existing Students", existing_students)

st.divider()




# --------------------------------------------------
# ENQUIRY REGISTRATION
# --------------------------------------------------

st.header("📝 New Enquiry Registration")

sources, programmes = get_dropdown_data()

if not sources:
    st.error("No active enquiry sources found in the database.")

elif not programmes:
    st.error("No active programmes found in the database.")

else:

    st.subheader("Student Information")

    student_name = st.text_input("Student Name *")
    father_name = st.text_input("Father's Name *")
    mobile_number = st.text_input("Mobile Number *")
    address = st.text_area("Address *")
    city = st.text_input("City *")

    # Check whether this mobile number already exists.
    existing_students = []

    if mobile_number.strip():
        existing_students = find_existing_mobile(
            mobile_number.strip()
        )

    confirm_new_student = False

    if existing_students:
        st.warning(
            "This mobile number is already associated with "
            "the following student record(s):"
        )

        for student in existing_students:
            st.write(
                f"Student: {student[1]} | "
                f"Father's Name: {student[2]}"
            )

        confirm_new_student = st.checkbox(
            "I have checked these records and confirm "
            "that this is a separate student."
        )

    st.divider()

    st.subheader("Enquiry Information")

    source_names = [row[1] for row in sources]

    selected_source = st.selectbox(
        "Enquiry Source *",
        source_names
    )

    programme_names = ["Not specified"] + [
        row[1] for row in programmes
    ]

    selected_programme = st.selectbox(
        "Programme Preference",
        programme_names
    )

    referrer_details = st.text_input(
        "Referrer Details (Optional)"
    )

    st.caption("* Mandatory fields")

    if st.button("Save Enquiry", type="primary"):

        # Validate mandatory fields
        if not all([
            student_name.strip(),
            father_name.strip(),
            mobile_number.strip(),
            address.strip(),
            city.strip()
        ]):
            st.error("Please fill in all mandatory student fields.")

        elif not mobile_number.strip().isdigit():
            st.error("Please enter a valid mobile number using digits only.")

        elif existing_students and not confirm_new_student:
            st.error(
                "Please confirm that this is a separate student "
                "after checking the existing records."
            )

        else:
            source_id = next(
                row[0] for row in sources
                if row[1] == selected_source
            )

            programme_id = None

            if selected_programme != "Not specified":
                programme_id = next(
                    row[0] for row in programmes
                    if row[1] == selected_programme
                )

            try:
                student_id, enquiry_id = save_enquiry(
                    student_name.strip(),
                    father_name.strip(),
                    mobile_number.strip(),
                    address.strip(),
                    city.strip(),
                    source_id,
                    programme_id,
                    referrer_details.strip()
                )

                st.success("Enquiry registered successfully!")

                st.write(f"**Student Record ID:** {student_id}")
                st.write(f"**Enquiry Record ID:** {enquiry_id}")

            except sqlite3.Error as error:
                st.error(f"Database error: {error}")


st.divider()
# --------------------------------------------------
# STUDENT MANAGEMENT
# --------------------------------------------------

st.divider()

st.header("👥 Student Management")

st.write(
    "Search student records and view their complete enquiry history."
)

search_text = st.text_input(
    "Search by Student Name, Mobile Number, ERP ID or Roll Number",
    key="student_search_input"
)

if st.button("Search Student", key="search_student_button"):

    if not search_text.strip():
        st.warning("Please enter a search term.")

    else:
        st.session_state["student_search_results"] = search_students(
            search_text
        )

        st.session_state["student_search_performed"] = True


# Display search results
if st.session_state.get("student_search_performed", False):

    results = st.session_state.get("student_search_results", [])

    if not results:
        st.warning("No matching student records found.")

    else:
        st.success(f"{len(results)} matching student record(s) found.")

        student_options = {
            row[0]: row for row in results
        }

        selected_student_id = st.selectbox(
            "Select a student to view details",
            options=list(student_options.keys()),
            format_func=lambda student_id: (
                f"{student_options[student_id][1]} "
                f"({student_options[student_id][3]})"
            )
        )

        student = student_options[selected_student_id]

        st.subheader("Student Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Student Name:** {student[1]}")
            st.write(f"**Father's Name:** {student[2]}")
            st.write(f"**Mobile Number:** {student[3]}")
            st.write(f"**City:** {student[4]}")

        with col2:
            st.write(f"**Student Type:** {student[5]}")
            st.write(
                f"**ERP Student Unique ID:** {student[6] or 'Not available'}"
            )
            st.write(
                f"**Roll Number:** {student[7] or 'Not available'}"
            )

        st.divider()

        st.subheader("Enquiry History")

        enquiry_history = get_student_enquiry_history(
            selected_student_id
        )

        if enquiry_history:

            st.subheader("Update Enquiry Status")

            # Create a dropdown containing this student's enquiries
            enquiry_options = {
                row[0]: row for row in enquiry_history
            }

            selected_enquiry_id = st.selectbox(
                "Select Enquiry",
                options=list(enquiry_options.keys()),
                format_func=lambda enquiry_id: (
                    f"Enquiry #{enquiry_id} - "
                    f"{enquiry_options[enquiry_id][1]} "
                    f"({enquiry_options[enquiry_id][3]})"
                ),
                key="selected_enquiry_status"
            )

            selected_enquiry = enquiry_options[selected_enquiry_id]
            current_status = selected_enquiry[3]

            st.write(f"**Current Status:** {current_status}")

            status_options = [
                "NEW",
                "CONTACTED",
                "INTERESTED",
                "NOT_INTERESTED",
                "FOLLOW_UP_REQUIRED",
                "CLOSED"
            ]

            new_status = st.selectbox(
                "Select New Status",
                status_options,
                index=status_options.index(current_status)
                if current_status in status_options else 0,
                key="new_enquiry_status"
            )

            if st.button("Update Enquiry Status", type="primary"):

                try:
                    updated = update_enquiry_status(
                        selected_enquiry_id,
                        new_status
                    )

                    if updated:
                        st.success(
                            f"Enquiry #{selected_enquiry_id} status "
                            f"updated to {new_status}."
                        )
                    else:
                        st.info("The enquiry already has this status.")

                    # Retrieve the latest enquiry history
                    enquiry_history = get_student_enquiry_history(
                        selected_student_id
                    )

                except (ValueError, sqlite3.Error) as error:
                    st.error(f"Unable to update status: {error}")

            st.divider()

            st.subheader("Complete Enquiry History")

            history_data = []

            for enquiry in enquiry_history:
                history_data.append({
                    "Enquiry ID": enquiry[0],
                    "Enquiry Source": enquiry[1],
                    "Programme": enquiry[2] or "Not specified",
                    "Status": enquiry[3],
                    "Enquiry Date": enquiry[4]
                })

            st.dataframe(
                history_data,
                width="stretch",
                hide_index=True
            )

            st.info(
                f"Total enquiries for this student: {len(enquiry_history)}"
            )

        else:
            st.info("No enquiry history found for this student.")

st.caption("IFTM EMS | Development Version")

# --------------------------------------------------
# CALLING ACTIVITY MANAGEMENT
# --------------------------------------------------

st.divider()

st.header("📞 Calling Activity Management")

st.write(
    "Record counselling calls, outcomes, remarks "
    "and next follow-up dates."
)

calling_enquiries = get_enquiries_for_calling()

if not calling_enquiries:

    st.info("No enquiries are available for calling.")

else:

    enquiry_options = {
        row[0]: row for row in calling_enquiries
    }

    selected_calling_enquiry = st.selectbox(
        "Select Student Enquiry",
        options=list(enquiry_options.keys()),
        format_func=lambda enquiry_id: (
            f"Enquiry #{enquiry_id} | "
            f"{enquiry_options[enquiry_id][1]} | "
            f"{enquiry_options[enquiry_id][2]} | "
            f"{enquiry_options[enquiry_id][3] or 'Programme not specified'}"
        ),
        key="calling_enquiry_selection"
    )

    selected_enquiry = enquiry_options[selected_calling_enquiry]

    st.write(f"**Student:** {selected_enquiry[1]}")
    st.write(f"**Mobile:** {selected_enquiry[2]}")
    st.write(f"**Programme:** {selected_enquiry[3] or 'Not specified'}")
    st.write(f"**Current Enquiry Status:** {selected_enquiry[4]}")

    st.divider()

    st.subheader("Record New Call")

    call_outcome_options = {
        "Answered": "ANSWERED",
        "No Answer": "NO_ANSWER",
        "Busy": "BUSY",
        "Switched Off": "SWITCHED_OFF",
        "Invalid Number": "INVALID_NUMBER",
        "Call Back Requested": "CALL_BACK_REQUESTED",
        "Other": "OTHER"
    }

    selected_call_outcome = st.selectbox(
        "Call Outcome",
        options=list(call_outcome_options.keys()),
        key="call_outcome_selection"
    )

    call_remarks = st.text_area(
        "Call Remarks",
        placeholder="Enter discussion details or call observations...",
        key="call_remarks"
    )

    follow_up_required = st.checkbox(
        "Schedule Next Follow-up",
        key="follow_up_required"
    )

    next_follow_up_date = None

    if follow_up_required:

        selected_follow_up_date = st.date_input(
            "Next Follow-up Date",
            key="next_follow_up_date"
        )

        next_follow_up_date = selected_follow_up_date.isoformat()

    if st.button("Save Call Activity", type="primary"):

        try:

            call_activity_id = save_call_activity(
                selected_calling_enquiry,
                call_outcome_options[selected_call_outcome],
                call_remarks.strip(),
                next_follow_up_date
            )

            st.success(
                f"Call activity saved successfully! "
                f"Call Activity ID: {call_activity_id}"
            )

        except (ValueError, sqlite3.Error) as error:

            st.error(f"Unable to save call activity: {error}")


st.divider()
# --------------------------------------------------
# CALLING HISTORY DISPLAY
# --------------------------------------------------

st.subheader("📋 Complete Calling History")

calling_history = get_calling_history(
    selected_calling_enquiry
)

if calling_history:

    history_data = []

    for call in calling_history:

        history_data.append({
            "Call ID": call[0],
            "Call Date & Time": call[1],
            "Call Outcome": call[2],
            "Remarks": call[3] or "-",
            "Next Follow-up": call[4] or "Not scheduled",
            "Recorded By": call[5]
        })

    st.dataframe(
        history_data,
        width="stretch",
        hide_index=True
    )

    st.info(
        f"Total calls recorded for this enquiry: "
        f"{len(calling_history)}"
    )

else:

    st.info("No calling history available for this enquiry.")
# --------------------------------------------------
# FOLLOW-UP MANAGEMENT DASHBOARD
# --------------------------------------------------

st.divider()

st.header("📅 Follow-up Management Dashboard")

st.write(
    "Monitor overdue, today's and upcoming student follow-ups."
)

follow_up_records = get_follow_up_tasks()

today = date.today()

overdue_records = []
today_records = []
upcoming_records = []

for record in follow_up_records:

    follow_up_date = date.fromisoformat(record[7])

    if follow_up_date < today:
        overdue_records.append(record)

    elif follow_up_date == today:
        today_records.append(record)

    else:
        upcoming_records.append(record)


# Dashboard summary metrics

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Overdue Follow-ups", len(overdue_records))

with col2:
    st.metric("Due Today", len(today_records))

with col3:
    st.metric("Upcoming Follow-ups", len(upcoming_records))


# Function to display follow-up records

def display_follow_up_records(records):

    if records:

        follow_up_data = []

        for record in records:

            follow_up_data.append({
                "Call ID": record[0],
                "Enquiry ID": record[1],
                "Student Name": record[2],
                "Mobile Number": record[3],
                "Programme": record[4] or "Not specified",
                "Last Call Outcome": record[5],
                "Remarks": record[6] or "-",
                "Follow-up Date": record[7],
                "Recorded By": record[8]
            })

        st.dataframe(
            follow_up_data,
            width="stretch",
            hide_index=True
        )

    else:
        st.info("No follow-up records in this category.")


# Overdue section

st.subheader("🔴 Overdue Follow-ups")
display_follow_up_records(overdue_records)

st.divider()


# Due today section

st.subheader("🟡 Follow-ups Due Today")
display_follow_up_records(today_records)

st.divider()


# Upcoming section

st.subheader("🟢 Upcoming Follow-ups")
display_follow_up_records(upcoming_records)

st.caption("IFTM EMS | Development Version")