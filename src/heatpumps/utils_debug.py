import streamlit as st
from streamlit import session_state as ss

def debug_refrigerant_state():
    st.subheader("🔍 Debug: Refrigerant and Simulation State")

    # General info
    st.markdown("#### Session Parameters")
    st.json(ss.hp.params)

    # Refrigerant setup
    setup = ss.hp.params.get("setup", {})
    fluids = ss.hp.params.get("fluids", {})
    st.markdown("#### Refrigerant Setup")
    st.write("Selected refrigerants:", setup)
    st.write("Fluid definitions:", fluids)

    # Network Results Check
    if hasattr(ss.hp, "nw") and hasattr(ss.hp.nw, "results"):
        conn = ss.hp.nw.results.get("Connection", pd.DataFrame())
        st.markdown("#### Network Connection Data (Preview)")
        st.dataframe(conn.head())

        # Available columns
        st.write("Available columns:", list(conn.columns))

        # Check fluid column values
        for wf_key in fluids.values():
            if wf_key in conn.columns:
                wfmask = conn[wf_key] == 1.0
                st.write(f"Fluid '{wf_key}' — Matching rows:", wfmask.sum())
                st.write("Sample 'h' values:", conn.loc[wfmask, "h"].dropna().head())
                st.write("Sample 'p' values:", conn.loc[wfmask, "p"].dropna().head())
                st.write("Sample 's' values:", conn.loc[wfmask, "s"].dropna().head())
            else:
                st.error(f"⚠️ Fluid column '{wf_key}' not found in network results.")
    else:
        st.error("❌ No network results found in `ss.hp.nw.results`.")

    # Sanity check on pressure and enthalpy for plotting
    try:
        h_vals = conn["h"].dropna()
        p_vals = conn["p"].dropna()
        s_vals = conn["s"].dropna()
        if h_vals.empty or p_vals.empty:
            st.warning("⚠️ Enthalpy or Pressure data is empty.")
        else:
            st.success("✅ Enthalpy and Pressure data present.")
    except Exception as e:
        st.error(f"Error checking values: {e}")
