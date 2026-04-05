import streamlit as st
import sqlite3
from datetime import date
import smtplib
from email.message import EmailMessage
import bcrypt
import random
import pandas as pd
import matplotlib.pyplot as plt

# --- PAGE CONFIG ---
st.set_page_config(page_title="Spice Delight", page_icon="🍽️", layout="wide")

# --- CUSTOM CSS (PRO UI) ---
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
.stButton>button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 10px;
    padding: 10px;
}
.stTextInput>div>div>input {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE ---
conn = sqlite3.connect("restaurant_pro.db", check_same_thread=False)
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
    password BLOB
)
""")
conn.commit()

# --- SAFE ADMIN CREATE ---
def create_admin():
    password = "admin123".encode()
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())

    c.execute("SELECT * FROM admin WHERE email=?", ("prathameshmore104@gmail.com",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO admin (email, password) VALUES (?, ?)",
            ("admin@gmail.com", hashed)
        )
        conn.commit()

create_admin()

# --- FUNCTIONS ---
def add_reservation(name, email, people, booking_date):
    c.execute(
        "INSERT INTO reservations (name, email, people, booking_date) VALUES (?, ?, ?, ?)",
        (name, email, people, booking_date)
    )
    conn.commit()

def get_reservations():
    c.execute("SELECT * FROM reservations")
    return c.fetchall()

def check_login(email, password):
    c.execute("SELECT password FROM admin WHERE email=?", (email,))
    result = c.fetchone()
    if result:
        return bcrypt.checkpw(password.encode(), result[0])
    return False

def update_password(email, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    c.execute("UPDATE admin SET password=? WHERE email=?", (hashed, email))
    conn.commit()

# --- EMAIL ---
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

# --- SIDEBAR ---
st.sidebar.title("🍽️ Spice Delight")
menu = st.sidebar.radio("Navigate", ["Home", "Book Table", "Admin"])

# --- HOME ---
if menu == "Home":
    st.title("✨ Welcome to Spice Delight")
    st.markdown("### Fine Dining Experience 🍷")
    st.image("https://images.unsplash.com/photo-1414235077428-338989a2e8c0")

# --- BOOK TABLE ---
elif menu == "Book Table":
    st.title("📅 Reserve Your Table")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Name")
        email = st.text_input("Email")

    with col2:
        people = st.number_input("People", 1, 20)
        booking_date = st.date_input("Date", min_value=date.today())

    if st.button("Reserve Table 🚀"):
        if name and email:
            add_reservation(name, email, people, str(booking_date))

            try:
                send_email(
                    email,
                    "Reservation Confirmed",
                    f"Hello {name}, your table for {people} people on {booking_date} is confirmed."
                )
                st.success("✅ Reservation Confirmed & Email Sent")
            except:
                st.warning("Booked but email failed")

        else:
            st.error("⚠️ Please fill all fields")

# --- ADMIN ---
elif menu == "Admin":
    st.title("🔐 Admin Panel")

    tab1, tab2 = st.tabs(["Login", "Reset Password"])

    # LOGIN
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if check_login(email, password):
                st.session_state["admin"] = True
                st.success("✅ Login Successful")
            else:
                st.error("❌ Invalid Credentials")

    # RESET PASSWORD
    with tab2:
        f_email = st.text_input("Admin Email")

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
        st.subheader("📊 Reservations Dashboard")

        data = get_reservations()

        if data:
            df = pd.DataFrame(data, columns=["ID", "Name", "Email", "People", "Date"])
            st.dataframe(df, use_container_width=True)

            st.subheader("📈 Bookings Chart")
            fig, ax = plt.subplots()
            df["People"].plot(kind="bar", ax=ax)
            st.pyplot(fig)

        else:
            st.info("No reservations yet")
