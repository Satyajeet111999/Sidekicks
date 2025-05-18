import streamlit as st
import sqlite3
import yagmail
from dotenv import load_dotenv
import os
import pandas as pd
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

def manager_dashboard():
    st.header("Manager Dashboard")
    manager = st.text_input("Enter your Manager Email to login")

    if manager:
        conn = sqlite3.connect("travel_requests.db")
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE manager=? AND status='Pending'", (manager,))
        rows = c.fetchall()

        if not rows:
            st.info("No pending requests.")
        else:
            df = pd.DataFrame(rows, columns=["ID", "Employee ID", "Employee Name", "From", "To", "Date", "Time", "Mode", "Manager", "Status"])
            st.dataframe(df, use_container_width=True)

            for row in rows:
                with st.expander(f"Request ID: {row[0]} - {row[2]}"):
                    st.write(f"From: {row[3]} → To: {row[4]}")
                    st.write(f"Date: {row[5]}, Time: {row[6]}, Mode: {row[7]}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Approve_{row[0]}"):
                            c.execute("UPDATE requests SET status='Approved' WHERE id=?", (row[0],))
                            conn.commit()
                            yag = yagmail.SMTP(EMAIL_USER)
                            link = "http://localhost:8501?dashboard=Admin"
                            yag.send(to="28satyajeet99@gmail.com", subject="Travel Booking Required", contents=f"Approved request:{row} Admin Dashboard: {link}")
                            st.success("Approved and email sent to admin.")
                    with col2:
                        if st.button(f"Reject_{row[0]}"):
                            c.execute("UPDATE requests SET status='Rejected' WHERE id=?", (row[0],))
                            conn.commit()
                            yag = yagmail.SMTP(EMAIL_USER)
                            yag.send(to=row[2], subject="Travel Request Rejected", contents=f"Your request from {row[3]} to {row[4]} was rejected.")
                            st.warning("Rejected and email sent to employee.")