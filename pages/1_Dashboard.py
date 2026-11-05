
import streamlit as st

from database.queries import get_dashboard_stats


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="IFTM EMS | Dashboard",
    page_icon="🎓",
    layout="wide"
)


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


# Fetch live statistics from the database

(
    total_enquiries,
    total_students,
    new_enquiries,
    existing_students
) = get_dashboard_stats()


# Display dashboard metrics

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
