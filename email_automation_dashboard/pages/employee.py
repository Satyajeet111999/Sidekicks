import streamlit as st
import sqlite3
import yagmail
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

def employee_dashboard():
    st.header("Employee Dashboard")
    emp_id = st.text_input("Enter Employee ID")
    emp_name = st.text_input("Enter Your Name")

    if emp_id and emp_name:
        source = st.text_input("Travel From")
        destination = st.text_input("Travel To")
        date = st.date_input("Travel Date")
        time = st.time_input("Travel Time")
        mode = st.selectbox("Mode of Travel", ["Flight", "Train", "Bus", "Car"])
        manager = st.selectbox("Select Manager", ["28satyajeet99@gmail.com", "manager2@example.com"])

        if st.button("Submit Travel Request"):
            conn = sqlite3.connect("travel_requests.db")
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS requests (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         emp_id TEXT, emp_name TEXT, source TEXT, destination TEXT, date TEXT, 
                         time TEXT, mode TEXT, manager TEXT, status TEXT)""")
            c.execute("INSERT INTO requests (emp_id, emp_name, source, destination, date, time, mode, manager, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (emp_id, emp_name, source, destination, str(date), str(time), mode, manager, "Pending"))
            conn.commit()
            conn.close()
            print(EMAIL_USER)
            yag = yagmail.SMTP(EMAIL_USER)
            link = f"http://localhost:8501?dashboard=Manager&manager={manager}"
            body = f"""New travel request from {emp_name}:
From: {source}
To: {destination}
Date: {date}
Time: {time}
Mode: {mode}

Approve or Reject here: {link}"""
            yag.send(to=manager, subject="New Travel Request", contents=body)
            st.success("Request sent to manager successfully!")
