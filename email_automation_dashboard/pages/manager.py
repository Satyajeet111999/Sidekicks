import os
import sqlite3
import pandas as pd
import streamlit as st
import yagmail
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Load environment variables and register email
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

MODE_ICONS = {
    "Car": "🚗", "Bus": "🚌", "Train": "🚆", "Flight": "✈️",
    "Bike": "🏍️", "Taxi": "🚕", "Metro": "🚇"
}

def render_pie_chart(df):
    status_counts = df["Status"].value_counts()
    st.write("Request Status Distribution:")
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = plt.cm.Paired(range(len(status_counts)))
    wedges, _, autotexts = ax.pie(
        status_counts,
        labels=status_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops={'fontsize': 12}
    )
    ax.set_title("Request Status Distribution", fontsize=16)
    ax.axis('equal')
    plt.setp(autotexts, size=12, weight="bold", color="white")
    st.pyplot(fig)

def update_request_status(c, conn, req_id, status):
    c.execute("UPDATE requests SET status=? WHERE id=?", (status, req_id))
    conn.commit()

def send_email(to, subject, contents):
    yag = yagmail.SMTP(EMAIL_USER)
    # Compose greeting and table
    greeting = "Dear Admin,<br><br>"
    if isinstance(contents, dict):
        # If contents is a dict, format as table
        table_rows = "".join(
            f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k, v in contents.items()
        )
        table_html = f"<table border='1' cellpadding='5'>{table_rows}</table><br>"
        body = greeting + "Please find the request details below:<br>" + table_html
    else:
        # Try to extract details from string if possible
        body = greeting + str(contents).replace('\n', '<br>')
    yag.send(to=to, subject=subject, contents=[body])

def handle_request_action(c, conn, row, action, is_dict=True):
    req_id = row['ID'] if is_dict else row[0]
    if action == "approve":
        update_request_status(c, conn, req_id, "Approved")
        link = "http://localhost:8501?dashboard=Admin"
        contents = (
            f"Approved request:\n{row.to_dict() if is_dict else row}\n\nAdmin Dashboard: {link}"
        )
        send_email("portal.automation8@gmail.com", "Travel Booking Required", contents)
        st.success("Approved and email sent to admin.")
    elif action == "reject":
        update_request_status(c, conn, req_id, "Rejected")
        if is_dict:
            contents = (
                f"Your travel request from {row['From']} to {row['To']} has been rejected."
            )
            send_email(row['Employee ID'], "Travel Request Rejected", contents)
        st.warning("Rejected and email sent to employee.")

def display_requests(df, c, conn):
    for _, row in df.iterrows():
        with st.expander(f"Request ID: {row['ID']} - {row['Employee Name']}"):
            st.write(f"From: {row['From']} → To: {row['To']}")
            st.write(f"Date: {row['Date']}, Time: {row['Time']}, Mode: {row['Mode']}")
            col1, col2 = st.columns(2)
            if col1.button(f"Approve_{row['ID']}"):
                handle_request_action(c, conn, row, "approve", is_dict=True)
            if col2.button(f"Reject_{row['ID']}"):
                handle_request_action(c, conn, row, "reject", is_dict=True)

def manager_dashboard():
    st.header("Manager Dashboard")
    manager_email = st.text_input("Enter your Manager Email to login")

    if not manager_email:
        return

    with sqlite3.connect("travel_requests.db") as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM requests WHERE manager=? AND status='Pending'",
            (manager_email,)
        )
        rows = c.fetchall()

        if not rows:
            st.info("No pending requests.")
            return

        columns = [
            "ID", "Employee ID", "Employee Name", "From", "To",
            "Date", "Time", "Mode", "Manager", "Status"
        ]
        df = pd.DataFrame(rows, columns=columns)
        df["Mode"] = df["Mode"].map(lambda x: f"{MODE_ICONS.get(x, '❓')} {x}")

        st.dataframe(
            df.style.set_properties(**{
                'background-color': '#f0f2f6',
                'color': '#222',
                'border-color': '#bbb'
            }).highlight_null('red'),
            use_container_width=True
        )
        render_pie_chart(df)
        display_requests(df, c, conn)
