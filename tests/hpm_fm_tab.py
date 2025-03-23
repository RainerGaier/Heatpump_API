import sqlite3
import pandas as pd
import streamlit as st
import bcrypt

DB_NAME = "heat_pump.db"


# ✅ Create tables if they do not exist
# Create Heat Pump Table
def create_hpm_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
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
    """
    )
    conn.commit()
    conn.close()

# Create User Table
def create_users_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Editor', 'Viewer'))
        );
    """
    )
    conn.commit()
    conn.close()


# Bootstrap users - count how many
def user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# Add User
def register_user(username, password, role):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pw, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

# Verify User
def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return row[1]  # Return role
    return None

# ✅ Read all data
def fetch_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM manufacturer_data", conn)
    conn.close()
    return df

# ✅ Read filtered data
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

# ✅ Insert new manufacturer
def insert_manufacturer(
    manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO manufacturer_data (manufacturer, model, mass_flow_kg_s, U_evap_W_m2K, U_cond_W_m2K, U_trans_W_m2K, efficiency, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost),
    )
    conn.commit()
    conn.close()

# ✅ Update an existing manufacturer
def update_manufacturer(
    id, manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE manufacturer_data
        SET manufacturer = ?, model = ?, mass_flow_kg_s = ?, U_evap_W_m2K = ?, U_cond_W_m2K = ?, U_trans_W_m2K = ?, efficiency = ?, cost_usd = ?
        WHERE id = ?;
        """,
        (manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost, id),
    )
    conn.commit()
    conn.close()

# ✅ Delete manufacturer by ID
def delete_manufacturer(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM manufacturer_data WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ✅ Export Data to CSV
def export_to_csv():
    df = fetch_all_data()
    df.to_csv("manufacturer_data_export.csv", index=False)
    return "manufacturer_data_export.csv"

# ✅ Import Data from CSV
def import_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    conn = sqlite3.connect(DB_NAME)
    df.to_sql("manufacturer_data", conn, if_exists="append", index=False)
    conn.close()


# --- MAIN SECTION ----
# Initialize databases
create_hpm_table()
create_users_table()


st.title("🔧 Heat Pump Manufacturer Database")


# 👇 Bootstrapping first user
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
                st.experimental_rerun()
            else:
                st.error("Username already exists.")

# --- Need to Log in ----
if "role" not in st.session_state:
    st.session_state.role = None

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
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

else:
    st.sidebar.success(
        f"Logged in as {st.session_state.username} ({st.session_state.role})"
    )


# if st.session_state.role in ["Admin", "Editor"]:
#     # show form
# else:
#     st.warning("Access denied.")



tabs = st.tabs(["🔍 View", "➕ Add", "✏️ Update", "❌ Delete", "📂 Import/Export"])

# --- View Tab ---
with tabs[0]:
    st.subheader("🔍 Search & View Data")
    search_text = st.text_input("Search by Manufacturer or Model")
    df_filtered = fetch_filtered_data(search_text)
    st.dataframe(df_filtered)

# --- Add Tab ---
with tabs[1]:
    st.subheader("➕ Add New Manufacturer")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            manufacturer = st.text_input("Manufacturer")
            model = st.text_input("Model")
            mass_flow = st.number_input("Mass Flow (kg/s)", min_value=0.1, step=0.1)
            efficiency = st.number_input(
                "Efficiency (0-1)", min_value=0.1, max_value=1.0, step=0.01
            )
        with col2:
            U_evap = st.number_input("U_evap (W/m²K)", min_value=0.0, step=10.0)
            U_cond = st.number_input("U_cond (W/m²K)", min_value=0.0, step=10.0)
            U_trans = st.number_input("U_trans (W/m²K)", min_value=0.0, step=10.0)
            cost = st.number_input("Cost (USD)", min_value=100.0, step=100.0)

        submit_new = st.form_submit_button("Add Manufacturer")

    if submit_new:
        insert_manufacturer(
            manufacturer, model, mass_flow, U_evap, U_cond, U_trans, efficiency, cost
        )
        st.success(f"Added {manufacturer} - {model}")
        st.experimental_rerun()

# --- Update Tab ---
with tabs[2]:
    st.subheader("✏️ Update Manufacturer")
    df = fetch_all_data()
    if not df.empty:
        update_id = st.selectbox("Select Manufacturer to Update", df["id"].astype(str))
        selected_row = df[df["id"].astype(str) == update_id].iloc[0]

        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                manufacturer = st.text_input(
                    "Manufacturer", value=selected_row["manufacturer"]
                )
                model = st.text_input("Model", value=selected_row["model"])
                mass_flow = st.number_input(
                    "Mass Flow (kg/s)",
                    value=selected_row["mass_flow_kg_s"],
                    min_value=0.1,
                    step=0.1,
                )
                efficiency = st.number_input(
                    "Efficiency (0-1)",
                    value=selected_row["efficiency"],
                    min_value=0.1,
                    max_value=1.0,
                    step=0.01,
                )
            with col2:
                U_evap = st.number_input(
                    "U_evap (W/m²K)",
                    value=selected_row["U_evap_W_m2K"],
                    min_value=0.0,
                    step=10.0,
                )
                U_cond = st.number_input(
                    "U_cond (W/m²K)",
                    value=selected_row["U_cond_W_m2K"],
                    min_value=0.0,
                    step=10.0,
                )
                U_trans = st.number_input(
                    "U_trans (W/m²K)",
                    value=selected_row["U_trans_W_m2K"],
                    min_value=0.0,
                    step=10.0,
                )
                cost = st.number_input(
                    "Cost (USD)",
                    value=selected_row["cost_usd"],
                    min_value=100.0,
                    step=100.0,
                )

            submit_update = st.form_submit_button("Update Manufacturer")

        if submit_update:
            update_manufacturer(
                update_id,
                manufacturer,
                model,
                mass_flow,
                U_evap,
                U_cond,
                U_trans,
                efficiency,
                cost,
            )
            st.success(f"Updated {manufacturer} - {model}")
            st.experimental_rerun()

# --- Delete Tab ---
with tabs[3]:
    st.subheader("❌ Delete Manufacturer")
    df = fetch_all_data()
    if not df.empty:
        delete_id = st.selectbox("Select Manufacturer to Delete", df["id"].astype(str))
        if st.button("Delete Manufacturer"):
            delete_manufacturer(delete_id)
            st.warning(f"Deleted Manufacturer ID {delete_id}")
            st.experimental_rerun()

# --- Import/Export Tab ---
with tabs[4]:
    st.subheader("📂 Export & Import Data")
    if st.button("Export Data to CSV"):
        file_path = export_to_csv()
        with open(file_path, "rb") as f:
            st.download_button(
                "Download CSV", f, file_name="manufacturer_data_export.csv"
            )

    uploaded_file = st.file_uploader("Upload CSV to Import Data", type="csv")
    if uploaded_file:
        import_from_csv(uploaded_file)
        st.success("Data imported successfully!")
        st.experimental_rerun()
