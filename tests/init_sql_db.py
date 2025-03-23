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

    # Add index for faster search
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_manufacturer_model ON manufacturer_data (manufacturer, model);"
    )
    conn.commit()
    conn.close()
