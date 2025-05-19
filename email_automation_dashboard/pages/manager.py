import os
import sqlite3
import pandas as pd
import streamlit as st
import yagmail
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import hashlib
import random

# Load environment variables and register email
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

MODE_ICONS = {
    "Car": "🚗", "Bus": "🚌", "Train": "🚆", "Flight": "✈️",
    "Bike": "🏍️", "Taxi": "🚕", "Metro": "🚇"
}

# Simple manager credentials (email: hashed_password)
MANAGER_CREDENTIALS = {
    "28satyajeet99@gmail.com": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # password: "password"
    "manager2@example.com": "12dea96fec20593566ab75692c9949596833adc9d660fa0b7b0e16b3fae00cab",  # password: "123456"
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

def send_verification_code(email, code):
    subject = "Your Verification Code"
    contents = f"Your verification code is: <b>{code}</b>"
    yag = yagmail.SMTP(EMAIL_USER)
    yag.send(to=email, subject=subject, contents=[contents])

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
            send_email(row["Employee Email"], "Travel Request Rejected", contents)
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

def manager_login():
    st.header("Manager Login")
    email = st.text_input("Manager Email")
    password = st.text_input("Password", type="password")

    # Inline buttons for Login, Forgot Password, and Sign Up
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 2])
    login_btn = col1.button("Login", use_container_width=True)
    col2.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True)  # Spacer for alignment

    forgot_btn = col3.button(
        "Forgot Password",
        key="forgot_btn",
        use_container_width=True,
        help="Forgot your password?",
    )
    signup_btn = col5.button(
        "Sign Up",
        key="signup_btn",
        use_container_width=True,
        help="New user? Sign up here.",
    )

    # Custom CSS for button colors
    st.markdown("""
        <style>
        div[data-testid="column"]:nth-of-type(3) button {
            background-color: #1a73e8 !important;
            color: white !important;
        }
        div[data-testid="column"]:nth-of-type(5) button {
            background-color: #34a853 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- LOGIN LOGIC ---
    if login_btn:
        hashed = hash_password(password)
        if email in MANAGER_CREDENTIALS and MANAGER_CREDENTIALS[email] == hashed:
            st.session_state["manager_authenticated"] = True
            st.session_state["manager_email"] = email
            st.success("Login successful!")
        else:
            st.error("Invalid credentials")
            st.stop()

    # --- FORGOT PASSWORD LOGIC ---
    if forgot_btn or st.session_state.get("reset_code"):
        # Step 1: Send code if not already sent
        if not email:
            st.error("Please enter a valid email.")
            st.stop()
        if forgot_btn and email:
            if email not in MANAGER_CREDENTIALS:
                st.error("Email not registered.")
                st.stop()
            code = str(random.randint(100000, 999999))
            st.session_state["reset_code"] = code
            st.session_state["reset_email"] = email
            send_verification_code(email, code)
            st.info("Verification code sent to your email.")

        # Step 2: Ask for code and new password
        if st.session_state.get("reset_code"):
            input_code = st.text_input("Enter the 6-digit verification code", key="reset_code_input")
            new_password = st.text_input("Enter new password", type="password", key="reset_new_pwd")
            confirm_btn = st.button("Confirm Reset")
            if confirm_btn:
                if input_code == st.session_state.get("reset_code"):
                    MANAGER_CREDENTIALS[st.session_state["reset_email"]] = hash_password(new_password)
                    st.success("Password reset successful! Please login with your new password.")
                    st.session_state.pop("reset_code", None)
                    st.session_state.pop("reset_email", None)
                    st.stop()
                else:
                    st.error("Invalid verification code.")
                    st.stop()
            st.stop()

    # --- SIGN UP LOGIC ---
    if signup_btn or st.session_state.get("signup_code"):
        if not email:
            st.error("Please enter a valid email.")
            st.stop()   
        # Step 1: Send code if not already sent
        if signup_btn and email:
            if email in MANAGER_CREDENTIALS:
                st.error("Email already registered.")
                st.stop()
            elif not email:
                st.error("Please enter a valid email.")
                st.stop()
            code = str(random.randint(100000, 999999))
            st.session_state["signup_code"] = code
            st.session_state["signup_email"] = email
            send_verification_code(email, code)
            st.info("Verification code sent to your email.")

        # Step 2: Ask for code and new password
        if st.session_state.get("signup_code"):
            input_code = st.text_input("Enter the 6-digit verification code for sign up", key="signup_code_input")
            new_password = st.text_input("Set your password", type="password", key="signup_new_pwd")
            confirm_btn = st.button("Confirm Sign Up")
            if confirm_btn:
                if input_code == st.session_state.get("signup_code"):
                    MANAGER_CREDENTIALS[st.session_state["signup_email"]] = hash_password(new_password)
                    st.success("Sign up successful! Please login.")
                    st.session_state.pop("signup_code", None)
                    st.session_state.pop("signup_email", None)
                    st.stop()
                else:
                    st.error("Invalid verification code.")
                    st.stop()
            st.stop()

    if not st.session_state.get("manager_authenticated"):
        st.stop()

# Call login at the top of your main function
def manager_dashboard():
    # manager_login()
    manager_email = st.session_state["user_email"]
    st.header("Manager Dashboard")

    tab1, tab2 = st.tabs(["Approve/reject requests", "Overview"])

    with sqlite3.connect("travel_requests.db") as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM requests WHERE manager=?",
            (manager_email,)
        )
        rows = c.fetchall()

        if not rows:
            st.info("No requests found")
            return

        columns = [
            "ID", "Employee ID", "Employee Name", "Employee Email", "From", "To",
            "Date", "Time", "Mode", "Manager", "Status"
        ]
        df = pd.DataFrame(rows, columns=columns)
        df["Mode"] = df["Mode"].map(lambda x: f"{MODE_ICONS.get(x, '❓')} {x}")

        # Tab 1: Approve/reject requests (only pending)
        with tab1:
            pending_df = df[df["Status"] == "Pending"]
            if pending_df.empty:
                st.info("No pending requests.")
            else:
                display_requests(pending_df, c, conn)

        # Tab 2: Overview (all requests + pie chart)
        with tab2:
            st.dataframe(
                df.style.set_properties(**{
                    'background-color': '#f0f2f6',
                    'color': '#222',
                    'border-color': '#bbb'
                }).highlight_null('red'),
                use_container_width=True
            )
            render_pie_chart(df)
