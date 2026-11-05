
import streamlit as st
import sqlite3

from database.queries import (
    get_dropdown_data,
    find_existing_mobile,
    save_enquiry
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="IFTM EMS | New Enquiry",
    page_icon="📝",
    layout="wide"
)


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("📝 New Enquiry Registration")

st.caption(
    "Register a new student and create a linked enquiry record."
)

st.divider()


# --------------------------------------------------
# LOAD MASTER DATA
# --------------------------------------------------

sources, programmes = get_dropdown_data()

if not sources:
    st.error("No active enquiry sources found in the database.")

elif not programmes:
    st.error("No active programmes found in the database.")

else:

    # --------------------------------------------------
    # STUDENT INFORMATION
    # --------------------------------------------------

    st.subheader("Student Information")

    student_name = st.text_input("Student Name *")
    father_name = st.text_input("Father's Name *")
    mobile_number = st.text_input("Mobile Number *")
    address = st.text_area("Address *")
    city = st.text_input("City *")

    # --------------------------------------------------
    # DUPLICATE MOBILE CHECK
    # --------------------------------------------------

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

    # --------------------------------------------------
    # ENQUIRY INFORMATION
    # --------------------------------------------------

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

    # --------------------------------------------------
    # SAVE ENQUIRY
    # --------------------------------------------------

    if st.button("Save Enquiry", type="primary"):

        if not all([
            student_name.strip(),
            father_name.strip(),
            mobile_number.strip(),
            address.strip(),
            city.strip()
        ]):
            st.error(
                "Please fill in all mandatory student fields."
            )

        elif not mobile_number.strip().isdigit():
            st.error(
                "Please enter a valid mobile number using digits only."
            )

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

                st.success(
                    "Enquiry registered successfully!"
                )

                st.write(f"**Student Record ID:** {student_id}")
                st.write(f"**Enquiry Record ID:** {enquiry_id}")

            except sqlite3.Error as error:
                st.error(f"Database error: {error}")


st.divider()
