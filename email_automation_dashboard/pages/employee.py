import streamlit as st
import sqlite3
import yagmail
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
yagmail.register(EMAIL_USER, EMAIL_PASSWORD)

def employee_dashboard():
    st.header("Employee Dashboard")
    emp_id = st.text_input("Enter Employee ID")
    emp_name = st.text_input("Enter Your Name")
    emp_email = st.text_input("Enter Your Email ID")
    if emp_email and not pd.Series([emp_email]).str.match(r"^[\w\.-]+@[\w\.-]+\.\w+$").bool():
        st.error("Please enter a valid email address.")

    if emp_id and emp_name and emp_email:
        tab1, tab2 = st.tabs(["Book Your Travel", "Insights"])
        with tab1:
            travel_details = get_travel_details()
            if st.button("Submit Travel Request"):
                if not emp_email.strip():
                    st.error("Employee Email is required.")
                elif not pd.Series([emp_email]).str.match(r"^[\w\.-]+@[\w\.-]+\.\w+$").bool():
                    st.error("Please enter a valid email address.")
                elif validate_inputs(emp_id, emp_name, travel_details):
                    if save_to_database(emp_id, emp_name, travel_details):
                        send_email_notification(emp_name, emp_id, travel_details, emp_email)
        with tab2:
            display_employee_chart(emp_id)


def get_travel_details():
    source = st.text_input("Travel From")
    destination = st.text_input("Travel To")
    date = st.date_input("Travel Date", min_value=datetime.today().date())
    time = st.time_input("Travel Time")
    mode = st.selectbox("Mode of Travel", ["Flight", "Train", "Bus", "Car"])
    manager = st.selectbox("Select Manager", ["portal.automation8@gmail.com", "manager2@example.com"])
    return {"source": source, "destination": destination, "date": date, "time": time, "mode": mode, "manager": manager}


def validate_inputs(emp_id, emp_name, travel_details):
    if not emp_id.strip():
        st.error("Employee ID is required.")
        return False
    if not emp_name.strip():
        st.error("Employee Name is required.")
        return False
    if not travel_details["source"].strip():
        st.error("Travel From is required.")
        return False
    if not travel_details["destination"].strip():
        st.error("Travel To is required.")
        return False
    if not travel_details["date"]:
        st.error("Travel Date is required.")
        return False
    if not travel_details["time"]:
        st.error("Travel Time is required.")
        return False
    if not travel_details["mode"]:
        st.error("Mode of Travel is required.")
        return False
    if not travel_details["manager"]:
        st.error("Manager selection is required.")
        return False
    return True


def save_to_database(emp_id, emp_name, travel_details):
    try:
        conn = sqlite3.connect("travel_requests.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS requests (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     emp_id TEXT, emp_name TEXT, source TEXT, destination TEXT, date TEXT, 
                     time TEXT, mode TEXT, manager TEXT, status TEXT)""")
        c.execute("INSERT INTO requests (emp_id, emp_name, source, destination, date, time, mode, manager, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (emp_id, emp_name, travel_details["source"], travel_details["destination"], str(travel_details["date"]), str(travel_details["time"]), travel_details["mode"], travel_details["manager"], "Pending"))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        conn.close()


def send_email_notification(emp_name, emp_id, travel_details, emp_email):
    try:
        yag = yagmail.SMTP(EMAIL_USER)
        # Transport mode logos (using emoji for simplicity)
        mode_logos = {
            "Flight": "✈️",
            "Train": "🚆",
            "Bus": "🚌",
            "Car": "🚗"
        }
        mode_logo = mode_logos.get(travel_details['mode'], "")
        button_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.4; color: #333;">
            <p style="font-size: 18px;">Respected Manager,</p>
            <p style="font-size: 18px;">I hope this message finds you well.</p>
            <p style="font-size: 18px;">Greetings of the day!</p>
            <p style="font-size: 18px; font-weight: bold; margin-bottom: 4px; margin-top: 4px;">
            New travel request for - Name: {emp_name} Emp ID: {emp_id}
            </p>
            <table style="border-collapse: collapse; width: 60%; margin: 4px 0;">
            <tr>
            <th style="border: 1px solid #ddd; padding: 8px; background: #f2f2f2;">Field</th>
            <th style="border: 1px solid #ddd; padding: 8px; background: #f2f2f2;">Details</th>
            </tr>
            <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">Route</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{travel_details['source']} TO {travel_details['destination']}</td>
            </tr>
            <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">Schedule</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{travel_details['date']} at {travel_details['time']}</td>
            </tr>
            <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">Mode</td>
            <td style="border: 1px solid #ddd; padding: 8px; font-size: 20px;">{mode_logo} {travel_details['mode']}</td>
            </tr>
            <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">Manager</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{travel_details['manager']}</td>
            </tr>
            </table>
            <p style="font-size: 16px;">Click the button below to approve or reject the request:</p>
            <a href="http://localhost:8501/#employee-dashboard" style="display: inline-block; padding: 12px 25px; font-size: 16px; color: white; background-color: #007BFF; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center;">Approve/Reject</a>
            </body>
        </html>
        """
        yag.send(
            to=travel_details["manager"],
            cc=emp_email,
            subject="New Travel Request",
            contents=button_html
        )
        st.success("Request sent to manager successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def display_employee_chart(emp_id):
    try:
        # Connect to the database and fetch travel request details for the given employee ID
        conn = sqlite3.connect("travel_requests.db")
        query = """SELECT date, status, COUNT(*) as request_count 
                   FROM requests 
                   WHERE emp_id = ? 
                   GROUP BY date, status"""
        df = pd.read_sql_query(query, conn, params=(emp_id,))
        conn.close()

        if df.empty:
            st.info("This is your first booking, wishing you a smooth and exciting journey ahead!")
        else:
            # Pivot the data to create a summary for statuses
            pivot_df = df.pivot(index='date', columns='status', values='request_count').fillna(0).reset_index()

            # Define a color scheme with contrasting colors for better visibility
            status_colors = alt.Scale(
                domain=['Pending', 'Approved', 'Rejected'],
                range=['#5bc0ff', '#33FF57', '#FF3333']  # light blue, green, red
            )

            # Plot the chart using Altair with the defined color scheme
            chart_data = pivot_df.melt(id_vars=['date'], var_name='Status', value_name='Request Count')
            chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('Request Count:Q', title='Number of Requests', scale=alt.Scale(domain=(0, chart_data['Request Count'].max() + 1))),
                color=alt.Color('Status:N', scale=status_colors, title='Request Status'),
                tooltip=['date:T', 'Status:N', 'Request Count:Q']
            ).properties(
                title=f"Travel Requests for Employee ID: {emp_id}",
                width=700,
                height=400
            )
            st.altair_chart(chart)

            # Display the raw data for better understanding
            #st.subheader("Detailed Travel Request Data")
            #st.dataframe(df)
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

