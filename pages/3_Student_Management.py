
import streamlit as st
import sqlite3

from database.queries import (
    search_students,
    get_student_enquiry_history,
    update_enquiry_status
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="IFTM EMS | Student Management",
    page_icon="👥",
    layout="wide"
)


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("👥 Student Management")

st.write(
    "Search student records and view their complete enquiry history."
)

st.divider()


# --------------------------------------------------
# STUDENT SEARCH
# --------------------------------------------------

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


# --------------------------------------------------
# DISPLAY SEARCH RESULTS
# --------------------------------------------------

if st.session_state.get("student_search_performed", False):

    results = st.session_state.get("student_search_results", [])

    if not results:
        st.warning("No matching student records found.")

    else:
        st.success(
            f"{len(results)} matching student record(s) found."
        )

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

        # --------------------------------------------------
        # STUDENT DETAILS
        # --------------------------------------------------

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
                f"**ERP Student Unique ID:** "
                f"{student[6] or 'Not available'}"
            )
            st.write(
                f"**Roll Number:** {student[7] or 'Not available'}"
            )

        st.divider()

        # --------------------------------------------------
        # ENQUIRY HISTORY
        # --------------------------------------------------

        st.subheader("Enquiry History")

        enquiry_history = get_student_enquiry_history(
            selected_student_id
        )

        if enquiry_history:

            # --------------------------------------------------
            # UPDATE ENQUIRY STATUS
            # --------------------------------------------------

            st.subheader("Update Enquiry Status")

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
                            f"Enquiry #{selected_enquiry_id} "
                            f"status updated to {new_status}."
                        )
                    else:
                        st.info(
                            "The enquiry already has this status."
                        )

                    # Refresh the enquiry history
                    enquiry_history = get_student_enquiry_history(
                        selected_student_id
                    )

                except (ValueError, sqlite3.Error) as error:
                    st.error(
                        f"Unable to update status: {error}"
                    )

            st.divider()

            # --------------------------------------------------
            # COMPLETE ENQUIRY HISTORY
            # --------------------------------------------------

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
                f"Total enquiries for this student: "
                f"{len(enquiry_history)}"
            )

        else:
            st.info("No enquiry history found for this student.")


st.caption("IFTM EMS | Development Version")
