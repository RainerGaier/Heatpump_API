import sqlite3

# Sample manufacturer data
manufacturers = [
    ("Bitzer", "ECH209", 0.5, 500, 450, 400, 0.85, 5000),
    ("Danfoss", "SH295", 0.8, 600, 500, 420, 0.88, 6500),
    ("Mitsubishi", "PUEH50", 0.6, 550, 470, 410, 0.87, 7000),
]

# Connect to database
conn = sqlite3.connect("heat_pump.db")
cursor = conn.cursor()

# Insert data
cursor.executemany(
    """
INSERT INTO manufacturer_data 
(manufacturer, model, mass_flow_kg_s, U_evap_W_m2K, U_cond_W_m2K, U_trans_W_m2K, efficiency, cost_usd)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
""",
    manufacturers,
)

# Commit and close
conn.commit()
conn.close()
