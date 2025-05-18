import streamlit as st
import sqlite3

def admin_dashboard():
    st.header("Admin Dashboard")

    conn = sqlite3.connect("travel_requests.db")
    c = conn.cursor()
    c.execute("SELECT * FROM requests WHERE status='Approved'")
    rows = c.fetchall()

    if not rows:
        st.info("No approved requests.")
    else:
        for row in rows:
            st.write(f"Employee: {row[2]} | Manager: {row[8]} | From: {row[3]} To: {row[4]} | Date: {row[5]} | Mode: {row[7]}")
            if st.button(f"Mark as Booked_{row[0]}"):
                c.execute("UPDATE requests SET status='Booked' WHERE id=?", (row[0],))
                conn.commit()
                st.success("Marked as booked.")
    conn.close()
