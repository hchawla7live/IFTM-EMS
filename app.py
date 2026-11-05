
import streamlit as st


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="IFTM EMS",
    page_icon="🎓",
    layout="wide"
)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

st.title("🎓 IFTM Enquiry Management System")

st.caption(
    "School of Computer Science and Applications | IFTM University"
)

st.divider()

st.header("Welcome to IFTM EMS")

st.write(
    """
    A centralised system for managing student enquiries,
    student records, faculty allocation, counselling
    activities and admission follow-ups.
    """
)

st.info(
    "Select a module from the navigation menu on the left "
    "to begin working with IFTM EMS."
)

st.subheader("Available Modules")

st.markdown(
    """
    - **Dashboard:** View enquiry and student statistics.
    - **New Enquiry:** Register prospective students.
    - **Student Management:** Search and manage student records.
    - **Enquiry Management:** Track enquiry progress.
    - **Calling Activities:** Record counselling calls.
    - **Follow-ups:** Manage pending follow-up activities.
    - **Faculty Allocation:** Assign enquiries to faculty.
    - **Reports:** View and analyse admission data.
    """
)
