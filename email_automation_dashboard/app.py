import streamlit as st
from pages.employee import employee_dashboard
from pages.manager import manager_dashboard
from pages.admin import admin_dashboard

st.set_page_config(page_title="Email Automation System", layout="wide")
st.title("Email Automation System")

page = st.sidebar.radio("Select Dashboard", ["Employee", "Manager", "Admin"])

if page == "Employee":
    employee_dashboard()
elif page == "Manager":
    manager_dashboard()
elif page == "Admin":
    admin_dashboard()
