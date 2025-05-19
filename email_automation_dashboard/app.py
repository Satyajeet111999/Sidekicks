import streamlit as st
import sqlite3
import random
import yagmail
import os
from pages.employee import employee_dashboard
from pages.manager import manager_dashboard, hash_password
from pages.admin import admin_dashboard

st.set_page_config(page_title="Email Automation System", layout="wide")
st.title("Email Automation System")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

CREDENTIALS_DB = "credentials.db"

def init_credentials_db():
    with sqlite3.connect(CREDENTIALS_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('Employee', 'Manager', 'Admin'))
            )
        """)
        conn.commit()

def get_user(email, user_type):
    with sqlite3.connect(CREDENTIALS_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT email, password, user_type FROM users WHERE email = ? AND user_type = ?", (email, user_type))
        return c.fetchone()

def add_user(email, password, user_type):
    with sqlite3.connect(CREDENTIALS_DB) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO users (email, password, user_type) VALUES (?, ?, ?)", (email, password, user_type))
        conn.commit()

def update_password(email, new_password):
    with sqlite3.connect(CREDENTIALS_DB) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()

def send_verification_code(email, code):
    subject = "Your Verification Code"
    contents = f"Your verification code is: <b>{code}</b>"
    yag = yagmail.SMTP(EMAIL_USER)
    yag.send(to=email, subject=subject, contents=[contents])

def unified_login():
    st.header("Login")
    user_type = st.selectbox("Login as", ["Employee", "Manager", "Admin"])
    email = st.text_input("Email")
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
        user = get_user(email, user_type)
        hashed = hash_password(password)
        if user and user[2] == user_type and user[1] == hashed:
            st.session_state["user_type"] = user_type
            st.session_state["user_email"] = email
            st.success(f"{user_type} login successful!")
            st.rerun()
        else:
            st.error(f"Invalid {user_type.lower()} credentials")
            st.stop()

    # --- FORGOT PASSWORD LOGIC ---
    if forgot_btn or st.session_state.get("reset_code"):
        if forgot_btn and email:
            user = get_user(email, user_type)
            if not user or user[2] != user_type:
                st.error("Email not registered for this user type.")
                st.stop()
            code = str(random.randint(100000, 999999))
            st.session_state["reset_code"] = code
            st.session_state["reset_email"] = email
            st.session_state["reset_user_type"] = user_type
            send_verification_code(email, code)
            st.info("Verification code sent to your email.")

        if st.session_state.get("reset_code") and st.session_state.get("reset_user_type") == user_type:
            input_code = st.text_input("Enter the 6-digit verification code", key="reset_code_input")
            new_password = st.text_input("Enter new password", type="password", key="reset_new_pwd")
            confirm_btn = st.button("Confirm Reset")
            if confirm_btn:
                if input_code == st.session_state.get("reset_code"):
                    update_password(st.session_state["reset_email"], hash_password(new_password))
                    st.success("Password reset successful! Please login with your new password.")
                    st.session_state.pop("reset_code", None)
                    st.session_state.pop("reset_email", None)
                    st.session_state.pop("reset_user_type", None)
                    st.stop()
                else:
                    st.error("Invalid verification code.")
                    st.stop()
            st.stop()

    # --- SIGN UP LOGIC ---
    if signup_btn or st.session_state.get("signup_code"):
        if signup_btn and email:
            user = get_user(email, user_type)
            if user:
                st.error("Email already registered.")
                st.stop()
            elif not email:
                st.error("Please enter a valid email.")
                st.stop()
            code = str(random.randint(100000, 999999))
            st.session_state["signup_code"] = code
            st.session_state["signup_email"] = email
            st.session_state["signup_user_type"] = user_type
            send_verification_code(email, code)
            st.info("Verification code sent to your email.")

        if st.session_state.get("signup_code") and st.session_state.get("signup_user_type") == user_type:
            input_code = st.text_input("Enter the 6-digit verification code for sign up", key="signup_code_input")
            new_password = st.text_input("Set your password", type="password", key="signup_new_pwd")
            confirm_btn = st.button("Confirm Sign Up")
            if confirm_btn:
                if input_code == st.session_state.get("signup_code"):
                    add_user(st.session_state["signup_email"], hash_password(new_password), user_type)
                    st.success("Sign up successful! Please login.")
                    st.session_state.pop("signup_code", None)
                    st.session_state.pop("signup_email", None)
                    st.session_state.pop("signup_user_type", None)
                    st.stop()
                else:
                    st.error("Invalid verification code.")
                    st.stop()
            st.stop()

    if not st.session_state.get("user_type"):
        st.stop()

# --- Initialize credentials DB on first run ---
init_credentials_db()

# --- Main Routing ---
if "user_type" not in st.session_state:
    unified_login()
else:
    if st.session_state["user_type"] == "Employee":

        employee_dashboard()
    elif st.session_state["user_type"] == "Manager":
        manager_dashboard()
    elif st.session_state["user_type"] == "Admin":
        admin_dashboard()
