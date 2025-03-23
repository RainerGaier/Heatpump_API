import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "heat_pump.db"

# Function to fetch manufacturer data from SQLite
def get_closest_match(mass_flow):
    conn = sqlite3.connect("heat_pump.db")
    cursor = conn.cursor()

    # Find closest match based on mass flow
    cursor.execute(
        """
        SELECT * FROM manufacturer_data 
        ORDER BY ABS(mass_flow_kg_s - ?) 
        LIMIT 1;
    """,
        (mass_flow,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "manufacturer": row[1],
            "model": row[2],
            "mass_flow_kg_s": row[3],
            "U_evap_W_m2K": row[4],
            "U_cond_W_m2K": row[5],
            "U_trans_W_m2K": row[6],
            "efficiency": row[7],
            "cost_usd": row[8],
        }
    return None


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


def import_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)

    conn = sqlite3.connect(DB_NAME)
    df.to_sql("manufacturer_data", conn, if_exists="append", index=False)
    conn.close()


def export_to_csv():
    df = fetch_all_data()
    df.to_csv("manufacturer_data_export.csv", index=False)
    return "manufacturer_data_export.csv"



# Streamlit UI
st.title("Heat Pump Cost Estimator with SQLite Database")

# User inputs
m_flash = st.slider("Select Refrigerant Mass Flow (kg/s)", 0.1, 2.0, 0.5)
t_res = st.slider("Select Flash Tank Residence Time (s)", 5, 30, 10)

st.subheader("📂 Export & Import Data")
if st.button("Export Data to CSV"):
    file_path = export_to_csv()
    st.success(f"Data exported successfully! Download it [here](/{file_path})")

uploaded_file = st.file_uploader("Upload CSV to Import Data", type="csv")

if uploaded_file:
    import_from_csv(uploaded_file)
    st.success("Data imported successfully!")
    st.experimental_rerun()


if st.button("Find Closest Manufacturer"):
    manufacturer_data = get_closest_match(m_flash)

    if manufacturer_data:
        df_results = pd.DataFrame(
            list(manufacturer_data.items()), columns=["Category", "Value"]
        )
        df_results["Value"] = df_results["Value"].astype(
            str
        )  # Convert all values to strings  
        st.dataframe(df_results)
    else:
        st.error("No manufacturer data found!")
