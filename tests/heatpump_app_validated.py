
import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from validators import is_required, is_numeric, is_percentage

DB_NAME = "heat_pump.db"

# ---------- DATABASE INIT ----------
def create_users_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Editor', 'Viewer'))
        );
    """)
    conn.commit()
    conn.close()

def create_manufacturer_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manufacturer_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            mass_flow_kg_s REAL NOT NULL,
            U_evap_W_m2K REAL NOT NULL,
            U_cond_W_m2K REAL NOT NULL,
            U_trans_W_m2K REAL NOT NULL,
            efficiency REAL NOT NULL,
            cost_usd REAL NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manufacturer_model ON manufacturer_data (manufacturer, model);")
    conn.commit()
    conn.close()

# ---------- USER AUTH ----------
def user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def register_user(username, password, role):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return row[1]
    return None

def delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# ---------- MANUFACTURER DATA ----------
def insert_manufacturer(manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO manufacturer_data (manufacturer, model, mass_flow_kg_s, U_evap_W_m2K, U_cond_W_m2K, U_trans_W_m2K, efficiency, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost))
    conn.commit()
    conn.close()

def fetch_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM manufacturer_data", conn)
    conn.close()
    return df

# ---------- INITIALIZATION ----------
create_users_table()
create_manufacturer_table()

# ---------- BOOTSTRAP ADMIN ----------
if "role" not in st.session_state:
    st.session_state.role = None

if user_count() == 0:
    st.warning("🛠 First-time setup: Create the initial Admin user")
    with st.form("bootstrap_admin"):
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Admin")
    if submitted:
        if password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password too short.")
        else:
            success = register_user(username, password, role="Admin")
            if success:
                st.success("Admin created. Please log in.")
                st.rerun()
            else:
                st.error("Username exists.")
    st.stop()

# ---------- LOGIN ----------
if st.session_state.role is None:
    st.title("🔐 Login to Heat Pump System")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
    if login_button:
        role = verify_user(username, password)
        if role:
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"Welcome {username} ({role})")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------- SETTINGS NAV ----------
st.sidebar.title("🔧 Settings")
settings_option = st.sidebar.radio("Go to", ["Heat Pump Maintenance", "User Administration"])

# ---------- HEAT PUMP TAB ----------
if settings_option == "Heat Pump Maintenance":
    tab1, tab2 = st.tabs(["➕ Add", "📊 View"])

    with tab1:
        st.subheader("➕ Add Manufacturer")
        with st.form("add_form"):
            manufacturer = st.text_input("Manufacturer")
            model = st.text_input("Model")
            mass_flow = st.text_input("Mass Flow (kg/s)")
            U_evap = st.text_input("U_evap (W/m²K)")
            U_cond = st.text_input("U_cond (W/m²K)")
            U_trans = st.text_input("U_trans (W/m²K)")
            efficiency = st.text_input("Efficiency (%)")
            cost = st.text_input("Cost (USD)")
            submitted = st.form_submit_button("Add Manufacturer")

        if submitted:
            errors = []
            if not is_required(manufacturer): errors.append("Manufacturer is required.")
            if not is_required(model): errors.append("Model is required.")
            if not is_numeric(mass_flow, 0): errors.append("Mass flow must be a positive number.")
            if not is_numeric(U_evap, 0): errors.append("U_evap must be a number.")
            if not is_numeric(U_cond, 0): errors.append("U_cond must be a number.")
            if not is_numeric(U_trans, 0): errors.append("U_trans must be a number.")
            if not is_percentage(efficiency): errors.append("Efficiency must be between 0 and 100.")
            if not is_numeric(cost, 100): errors.append("Cost must be ≥ $100.")

            if errors:
                for msg in errors:
                    st.error(msg)
            else:
                insert_manufacturer(
                    manufacturer, model,
                    float(mass_flow),
                    float(U_evap),
                    float(U_cond),
                    float(U_trans),
                    float(efficiency),
                    float(cost)
                )
                st.success("Manufacturer added successfully.")
                st.rerun()

    with tab2:
        st.subheader("📊 Manufacturer Data")
        df = fetch_all_data()
        st.dataframe(df)
