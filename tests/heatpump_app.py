# Generate the full Streamlit application code for managing the heat pump system and user administration


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

def user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ---------- USER AUTHENTICATION ----------

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

# ---------- MANUFACTURER DATA FUNCTIONS ----------

def fetch_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM manufacturer_data", conn)
    conn.close()
    return df

def fetch_filtered_data(search_text=""):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM manufacturer_data"
    params = ()
    if search_text:
        query += " WHERE manufacturer LIKE ? OR model LIKE ?"
        params = (f"%{search_text}%", f"%{search_text}%")
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def insert_manufacturer(manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO manufacturer_data (manufacturer, model, mass_flow_kg_s, U_evap_W_m2K, U_cond_W_m2K, U_trans_W_m2K, efficiency, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost))
    conn.commit()
    conn.close()

def update_manufacturer(id, manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE manufacturer_data
        SET manufacturer = ?, model = ?, mass_flow_kg_s = ?, U_evap_W_m2K = ?, U_cond_W_m2K = ?, U_trans_W_m2K = ?, efficiency = ?, cost_usd = ?
        WHERE id = ?;
    """, (manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost, id))
    conn.commit()
    conn.close()

def delete_manufacturer(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM manufacturer_data WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def export_to_csv():
    df = fetch_all_data()
    df.to_csv("manufacturer_data_export.csv", index=False)
    return "manufacturer_data_export.csv"

def import_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    conn = sqlite3.connect(DB_NAME)
    df.to_sql("manufacturer_data", conn, if_exists="append", index=False)
    conn.close()


def validate_manufacturer_inputs(data):
    """
    Validate manufacturer form fields. Expects a dictionary of form inputs as strings.
    Returns a tuple: (errors, parsed_values)
    """
    errors = []
    parsed = {}

    # Validate required fields
    if not is_required(data.get("manufacturer")):
        errors.append("Manufacturer is required.")
    if not is_required(data.get("model")):
        errors.append("Model is required.")

    # Validate numeric values
    for field, min_val in [
        ("mass_flow", 0),
        ("U_evap", 0),
        ("U_cond", 0),
        ("U_trans", 0),
        ("cost", 100),
    ]:
        value = data.get(field)
        if not is_numeric(value, min_val):
            errors.append(f"{field.replace('_', ' ').title()} must be ≥ {min_val}.")
        else:
            parsed[field] = float(value)

    # Validate percentage
    efficiency = data.get("efficiency")
    if not is_percentage(efficiency):
        errors.append("Efficiency must be a number between 0 and 100.")
    else:
        parsed["efficiency"] = float(efficiency)

    parsed["manufacturer"] = data.get("manufacturer")
    parsed["model"] = data.get("model")

    return errors, parsed


# ---------- APP UI ----------

create_users_table()
create_manufacturer_table()

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
            st.error("Password too short. Minimum 6 characters.")
        else:
            success = register_user(username, password, role="Admin")
            if success:
                st.success("Initial Admin user created. Please log in.")
                st.rerun()
            else:
                st.error("Username already exists.")
    st.stop()

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
            st.success(f"Welcome, {username}! Role: {role}")
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.stop()

# ---------- SIDEBAR NAV ----------
st.sidebar.title("🔧 Settings")
settings_option = st.sidebar.radio("Go to", ["Heat Pump Maintenance", "User Administration"])

# ---------- HEAT PUMP TABS ----------
if settings_option == "Heat Pump Maintenance":
    view_tab,add_tab, update_tab, delete_tab, imp_exp_tab = st.tabs(
        ["🔍 View", "➕ Add", "✏️ Update", "❌ Delete", "📦 Import/Export"]
    )

    # --- View Tab ---
    with view_tab:
        st.subheader("🔍 Search & View Data")
        search_text = st.text_input("Search by Manufacturer or Model")
        df_filtered = fetch_filtered_data(search_text)
        st.dataframe(df_filtered)

    # --- Add Tab ---
    with add_tab:
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

        # --- If filled in - Validate ---
        if submitted:
            form_data = {
                "manufacturer": manufacturer,
                "model": model,
                "mass_flow": mass_flow,
                "U_evap": U_evap,
                "U_cond": U_cond,
                "U_trans": U_trans,
                "efficiency": efficiency,
                "cost": cost,
            }

            errors, parsed = validate_manufacturer_inputs(form_data)

            if errors:
                for msg in errors:
                    st.error(msg)
            else:
                insert_manufacturer(
                    parsed["manufacturer"],
                    parsed["model"],
                    parsed["mass_flow"],
                    parsed["U_evap"],
                    parsed["U_cond"],
                    parsed["U_trans"],
                    parsed["efficiency"],
                    parsed["cost"],
                )
                st.success("Manufacturer added successfully.")
                st.rerun()

    with update_tab:
        st.subheader("✏️ Update Manufacturer")
        df = fetch_all_data()
        if not df.empty:
            update_id = st.selectbox("Select Manufacturer ID", df["id"])
            selected_row = df[df["id"] == update_id].iloc[0]
            with st.form("update_form"):
                # manufacturer = st.text_input("Manufacturer")
                # model = st.text_input("Model")
                # mass_flow = st.text_input("Mass Flow (kg/s)")
                # U_evap = st.text_input("U_evap (W/m²K)")
                # U_cond = st.text_input("U_cond (W/m²K)")
                # U_trans = st.text_input("U_trans (W/m²K)")
                # efficiency = st.text_input("Efficiency (%)")
                # cost = st.text_input("Cost (USD)")
                manufacturer = st.text_input("Manufacturer", value=selected_row["manufacturer"])
                model = st.text_input("Model", value=selected_row["model"])
                mass_flow = st.number_input("Mass Flow (kg/s)", value=selected_row["mass_flow_kg_s"], min_value=0.1)
                efficiency = st.number_input("Efficiency (0-1)", value=selected_row["efficiency"], min_value=0.1, max_value=1.0)
                U_evap = st.number_input("U_evap (W/m²K)", value=selected_row["U_evap_W_m2K"])
                U_cond = st.number_input("U_cond (W/m²K)", value=selected_row["U_cond_W_m2K"])
                U_trans = st.number_input("U_trans (W/m²K)", value=selected_row["U_trans_W_m2K"])
                cost = st.number_input("Cost (USD)", value=selected_row["cost_usd"])
                submit_update = st.form_submit_button("Update")

            if submit_update:
                form_data = {
                    "manufacturer": manufacturer,
                    "model": model,
                    "mass_flow": mass_flow,
                    "U_evap": U_evap,
                    "U_cond": U_cond,
                    "U_trans": U_trans,
                    "efficiency": efficiency,
                    "cost": cost,
                }

                errors, parsed = validate_manufacturer_inputs(form_data)

                if errors:
                    for msg in errors:
                        st.error(msg)
                else:
                    update_manufacturer(
                        update_id,
                        parsed["manufacturer"],
                        parsed["model"],
                        parsed["mass_flow"],
                        parsed["U_evap"],
                        parsed["U_cond"],
                        parsed["U_trans"],
                        parsed["efficiency"],
                        parsed["cost"],
                    )
                    st.success("Manufacturer updated successfully.")
                    st.rerun()

    with delete_tab:
        st.subheader("❌ Delete Manufacturer")
        df = fetch_all_data()
        if not df.empty:
            delete_id = st.selectbox("Select Manufacturer ID to Delete", df["id"])
            if st.button("Delete Manufacturer"):
                delete_manufacturer(delete_id)
                st.warning("Manufacturer deleted.")
                st.rerun()

    with imp_exp_tab:
        st.subheader("📦 Export & Import")
        if st.button("Export to CSV"):
            path = export_to_csv()
            st.success(f"Exported to {path}")
        file = st.file_uploader("Upload CSV", type="csv")
        if file:
            import_from_csv(file)
            st.success("Data imported.")
            st.rerun()

# ---------- USER ADMIN TABS ----------
if settings_option == "User Administration":
    if st.session_state.role != "Admin":
        st.error("Access Denied. Only Admins can manage users.")
    else:
        tab_user, tab_add = st.tabs(["📋 View & Manage Users", "➕ Add User"])

        with tab_user:
            st.subheader("📋 Registered Users")
            users_df = pd.read_sql("SELECT id, username, role FROM users", sqlite3.connect(DB_NAME))
            st.dataframe(users_df)
            delete_id = st.selectbox("Select User ID to Delete", users_df["id"])
            if st.button("Delete Selected User"):
                delete_user(delete_id)
                st.warning("User deleted.")
                st.rerun()

        with tab_add:
            st.subheader("➕ Add New User")
            with st.form("add_user_form"):
                new_user = st.text_input("Username")
                new_pw = st.text_input("Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")
                role = st.selectbox("Role", ["Admin", "Editor", "Viewer"])
                submitted = st.form_submit_button("Add User")
            if submitted:
                if new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    success = register_user(new_user, new_pw, role)
                    if success:
                        st.success("User added.")
                        st.rerun()
                    else:
                        st.error("Username already exists.")
