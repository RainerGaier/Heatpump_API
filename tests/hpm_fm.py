import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = "heat_pump.db"


# ✅ Create table if it doesn't exist
def create_table():
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

# Export Data
def export_to_csv():
    df = fetch_all_data()
    df.to_csv("manufacturer_data_export.csv", index=False)
    return "manufacturer_data_export.csv"


# Import Data
def import_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)

    conn = sqlite3.connect(DB_NAME)
    df.to_sql("manufacturer_data", conn, if_exists="append", index=False)
    conn.close()


# Initialize database
create_table()

st.title("Heat Pump Manufacturer Database Management")

# Load data
df = fetch_all_data()

# 🎯 Section: Search and Display Manufacturer Data
st.subheader("🔍 Search & Filter Manufacturer Data")
search_text = st.text_input("Search by Manufacturer or Model")

df_filtered = fetch_filtered_data(search_text)
st.dataframe(df_filtered)


# # 🎯 Section 1: Display Manufacturer Data
# st.subheader("📊 View Manufacturer Data")
# st.dataframe(df)
st.markdown("---")

# 🎯 Section 2: Add New Manufacturer
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

st.markdown("---")

# 🎯 Section 3: Update Manufacturer
st.subheader("✏️ Update Manufacturer")
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
st.markdown("---")

# 🎯 Section 4: Delete Manufacturer
st.subheader("❌ Delete Manufacturer")
if not df.empty:
    delete_id = st.selectbox("Select Manufacturer to Delete", df["id"].astype(str))
    if st.button("Delete Manufacturer"):
        delete_manufacturer(delete_id)
        st.warning(f"Deleted Manufacturer ID {delete_id}")
        st.experimental_rerun()
st.markdown("---")

st.subheader("📂 Export & Import Data")
if st.button("Export Data to CSV"):
    file_path = export_to_csv()
    st.success(f"Data exported successfully! Download it [here](/{file_path})")

uploaded_file = st.file_uploader("Upload CSV to Import Data", type="csv")

if uploaded_file:
    import_from_csv(uploaded_file)
    st.success("Data imported successfully!")
    st.experimental_rerun()

st.markdown("---")
