import streamlit as st
import pandas as pd
import numpy as np


# Dummy function to simulate loading manufacturer data
def load_manufacturer_data():
    """Simulate loading manufacturer data from CSV."""
    data = {
        "Manufacturer": ["Bitzer", "Danfoss", "Mitsubishi"],
        "Model": ["ECH209", "SH295", "PUEH50"],
        "MassFlow_kg_s": [0.5, 0.8, 0.6],
        "U_evap_W_m2K": [500, 600, 550],
        "U_cond_W_m2K": [450, 500, 470],
        "U_trans_W_m2K": [400, 420, 410],
        "Efficiency": [0.85, 0.88, 0.87],
        "Cost_USD": [5000, 6500, 7000],
    }
    return pd.DataFrame(data)


# Load manufacturer data
manufacturer_data = load_manufacturer_data()


def get_closest_match(mass_flow):
    """Find the closest manufacturer model based on mass flow rate."""
    manufacturer_data["MassFlow_Diff"] = abs(
        manufacturer_data["MassFlow_kg_s"] - mass_flow
    )
    closest_match = manufacturer_data.loc[manufacturer_data["MassFlow_Diff"].idxmin()]
    return closest_match


def calculate_operating_cost(Q_loss, eta, C_electricity, time_period="hour"):
    """Calculates operating cost for different time periods."""
    C_operating_hourly = (Q_loss / eta) * C_electricity
    time_multipliers = {"hour": 1, "day": 24, "month": 24 * 30, "year": 24 * 365}
    return C_operating_hourly * time_multipliers.get(time_period, 1)


def calculate_heat_pump_cost(
    manufacturer,
    model,
    m_flash,
    t_res,
    rho_flash,
    C_material,
    C_installation,
    Q_loss,
    C_electricity,
    time_period,
):
    """Compute the total cost of a heat pump using manufacturer data."""
    # Load manufacturer specs
    manufacturer_specs = get_closest_match(m_flash)

    # Extract real-world values
    U_evap = manufacturer_specs["U_evap_W_m2K"]
    U_cond = manufacturer_specs["U_cond_W_m2K"]
    U_trans = manufacturer_specs["U_trans_W_m2K"]
    eta = manufacturer_specs["Efficiency"]
    cost_model = manufacturer_specs["Cost_USD"]

    # Calculate flash tank volume
    V_tank = (m_flash * t_res) / rho_flash

    # Flash tank cost
    C_flash = (C_material * V_tank) + C_installation

    # Heat exchanger costs (using manufacturer specs)
    C_evap = U_evap * 50 * 10  # Example area * deltaT
    C_cond = U_cond * 40 * 12
    C_trans = U_trans * 30 * 15

    # Capital cost
    C_capital = C_evap + C_cond + C_trans + C_flash + cost_model

    # Operating cost for the selected time period
    C_operating = calculate_operating_cost(Q_loss, eta, C_electricity, time_period)

    # Total cost
    C_total = C_capital + C_operating

    return {
        "Selected Manufacturer": manufacturer_specs["Manufacturer"],
        "Selected Model": manufacturer_specs["Model"],
        "Flash Tank Volume (m³)": V_tank,
        "Flash Tank Cost ($)": C_flash,
        "Capital Cost ($)": C_capital,
        f"Operating Cost ({time_period}) ($)": C_operating,
        "Total Cost ($)": C_total,
    }


# Streamlit UI
st.title("Heat Pump Cost Estimator with Manufacturer Data")

# User inputs
m_flash = st.slider("Select Refrigerant Mass Flow (kg/s)", 0.1, 2.0, 0.5)
t_res = st.slider("Select Flash Tank Residence Time (s)", 5, 30, 10)
rho_flash = 1000  # Fixed for simplicity
C_material = 200
C_installation = 5000
Q_loss = 5
C_electricity = 0.15

# Time period selection
time_period = st.selectbox(
    "Select Time Period for Operating Cost", ["hour", "day", "month", "year"]
)

if st.button("Calculate Cost"):
    heat_pump_costs = calculate_heat_pump_cost(
        "Bitzer",
        "ECH209",
        m_flash,
        t_res,
        rho_flash,
        C_material,
        C_installation,
        Q_loss,
        C_electricity,
        time_period,
    )

    # Convert results to DataFrame
    df_results = pd.DataFrame(heat_pump_costs.items(), columns=["Category", "Value"])

    # **✅ Fix: Convert all values to string to prevent serialization error**
    df_results["Value"] = df_results["Value"].astype(str)

    # Display results
    st.subheader("Calculation Results")
    st.dataframe(df_results)
