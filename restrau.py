import streamlit as st
import sqlite3
from datetime import date
import smtplib
from email.message import EmailMessage
from passlib.hash import bcrypt
import random
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIG ---
st.set_page_config(page_title="Spice Delight", page_icon="🍽️", layout="wide")

# --- DATABASE ---
conn = sqlite3.connect("restaurant_final.db", check_same_thread=False)
c = conn.cursor()

# --- TABLES ---
c.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    people INTEGER,
    booking_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    email TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

# --- CREATE YOUR ADMIN ---
def create_admin():
    my_email = "meprathamesh21@gmail.com"
    password = "123"

    hashed = bcrypt.hash(password)

    c.execute("SELECT * FROM admin WHERE email=?", (my_email,))
    if not c.fetchone():
        c.execute(
            "INSERT INTO admin (email, password) VALUES (?, ?)",
            (my_email, hashed)
        )
        conn.commit()

create_admin()

# --- FUNCTIONS ---
def add_reservation(name, email, people, booking_date):
    c.execute(
        "INSERT INTO reservations (name, email, people, booking_date) VALUES (?, ?, ?, ?)",
        (name, email, people, str(booking_date))
    )
    conn.commit()

def get_reservations():
    c.execute("SELECT * FROM reservations")
    return c.fetchall()

def check_login(email, password):
    c.execute("SELECT password FROM admin WHERE email=?", (email,))
    result = c.fetchone()
    if result:
        return bcrypt.verify(password, result[0])
    return False

def update_password(email, new_password):
    hashed = bcrypt.hash(new_password)
    c.execute("UPDATE admin SET password=? WHERE email=?", (hashed, email))
    conn.commit()

def send_email(to_email, subject, body):
    sender_email = "meprathamesh21@gmail.com"
    app_password = "hrmk pksc ddwn ukmd"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)

# --- UI ---
st.sidebar.title("🍽️ Spice Delight")
menu = st.sidebar.radio("Menu", ["Home", "Book Table", "Admin"])

# --- HOME ---
if menu == "Home":
    st.title("✨ Spice Delight Restaurant")
    st.write("Premium Dining Experience 🍷")

# --- BOOK TABLE ---
elif menu == "Book Table":
    st.header("📅 Reserve Table")

    name = st.text_input("Name")
    email = st.text_input("Email")
    people = st.number_input("People", 1, 20)
    booking_date = st.date_input("Date", min_value=date.today())

    if st.button("Reserve"):
        if name and email:
            add_reservation(name, email, people, booking_date)

            try:
                send_email(
                    email,
                    "Reservation Confirmed",
                    f"Hello {name}, your table for {people} people on {booking_date} is confirmed."
                )
                st.success("Booked & Email Sent ✅")
            except:
                st.warning("Booked but email failed")

        else:
            st.error("Fill all fields")

# --- ADMIN ---
elif menu == "Admin":
    st.header("🔐 Admin Panel")

    tab1, tab2 = st.tabs(["Login", "Reset Password"])

    # LOGIN
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if check_login(email, password):
                st.session_state["admin"] = True
                st.success("Login Successful")
            else:
                st.error("Invalid Credentials")

    # RESET PASSWORD
    with tab2:
        f_email = st.text_input("Enter Email")

        if st.button("Send OTP"):
            otp = random.randint(1000, 9999)
            st.session_state["otp"] = str(otp)
            st.session_state["reset_email"] = f_email

            try:
                send_email(f_email, "OTP", f"Your OTP is {otp}")
                st.success("OTP Sent")
            except:
                st.error("Email failed")

        entered = st.text_input("Enter OTP")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Reset Password"):
            if entered == st.session_state.get("otp"):
                update_password(st.session_state["reset_email"], new_pass)
                st.success("Password Updated")
            else:
                st.error("Wrong OTP")

    # DASHBOARD
    if st.session_state.get("admin"):
        st.subheader("📊 Reservations")

        data = get_reservations()

        if data:
            df = pd.DataFrame(data, columns=["ID", "Name", "Email", "People", "Date"])
            st.dataframe(df)

            fig, ax = plt.subplots()
            df["People"].plot(kind="bar", ax=ax)
            st.pyplot(fig)
        else:
            st.info("No data yet")
