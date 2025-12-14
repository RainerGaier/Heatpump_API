import json
import os
import uuid
from datetime import datetime

import darkdetect
import httpx
import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np
import pandas as pd
import streamlit as st
from CoolProp.CoolProp import PropsSI as PSI
from streamlit import session_state as ss

# Use absolute imports when installed as package
try:
    import heatpumps.variables as var
    from heatpumps.simulation import run_design, run_partload
    from heatpumps.streamlit_helpers import extract_report_data
except ImportError:
    # Fallback for direct script execution
    import variables as var
    from simulation import run_design, run_partload
    from streamlit_helpers import extract_report_data


def debug_refrigerant_state(mode="None"):
    """
    Debug refrigerant setup and TESPy result data integrity.

    Parameters
    ----------
    mode : str
        One of 'None', 'Streamlit', or 'Console'. Controls how and if debug output is shown.
    """
    if mode == "None":
        return  # Skip all debug output

    import pprint

    def log(msg, level="info"):
        if mode == "Streamlit":
            if level == "info":
                st.info(msg)
            elif level == "success":
                st.success(msg)
            elif level == "warning":
                st.warning(msg)
            elif level == "error":
                st.error(msg)
        else:
            print(f"[{level.upper()}] {msg}")

    def log_dataframe(df, caption=None):
        if mode == "Streamlit":
            st.dataframe(df, use_container_width=True)
        else:
            print(f"\n--- {caption or 'Data Preview'} ---")
            print(df.head())

    log("🔍 DEBUG: REFRIGERANT AND SIMULATION STATE")

    # Print full parameter setup
    log("▶️ Session Parameters:", level="info")
    if hasattr(ss, "hp") and hasattr(ss.hp, "params"):
        if mode == "Console":
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(ss.hp.params)
        else:
            st.json(ss.hp.params)
    else:
        log("❌ ss.hp or ss.hp.params not found.", level="error")
        return

    setup = ss.hp.params.get("setup", {})
    fluids = ss.hp.params.get("fluids", {})
    log(f"▶️ Refrigerant Setup: {setup}")
    log(f"▶️ Fluid definitions: {fluids}")

    # Check network results
    if hasattr(ss.hp, "nw") and hasattr(ss.hp.nw, "results"):
        conn = ss.hp.nw.results.get("Connection", pd.DataFrame())
        if conn.empty:
            log("⚠️ Network Connection DataFrame is empty", level="warning")
        else:
            log("▶️ Network Connection Data (Preview):")
            log_dataframe(conn, caption="Connection Data Preview")

            log(f"Available columns: {list(conn.columns)}")

            for wf_key in fluids.values():
                if wf_key in conn.columns:
                    wfmask = conn[wf_key] == 1.0
                    log(f"✅ Fluid '{wf_key}' — Matching rows: {wfmask.sum()}")
                    if wfmask.sum() > 0:
                        log(
                            f"Sample 'h': {conn.loc[wfmask, 'h'].dropna().head().tolist()}"
                        )
                        log(
                            f"Sample 'p': {conn.loc[wfmask, 'p'].dropna().head().tolist()}"
                        )
                        log(
                            f"Sample 's': {conn.loc[wfmask, 's'].dropna().head().tolist()}"
                        )
                else:
                    log(
                        f"⚠️ Fluid column '{wf_key}' not found in results.",
                        level="warning",
                    )
    else:
        log("❌ No network results found in `ss.hp.nw.results`.", level="error")
        return

    try:
        h_vals = conn["h"].dropna()
        p_vals = conn["p"].dropna()
        if h_vals.empty or p_vals.empty:
            log("⚠️ Enthalpy or Pressure data is empty.", level="warning")
        else:
            log("✅ Enthalpy and Pressure data present.", level="success")
    except Exception as e:
        log(f"❌ Error checking values: {e}", level="error")

def switch2design():
    """Switch to design simulation tab."""
    ss.select = 'Configuration'


def exit_app():
    st.write("Exiting the application...")
    os.system("taskkill /F /IM python.exe")  # Windows
    st.stop()  # This stops Streamlit execution
    os._exit(0)  # Forcefully exit Python if running in a script


def switch2partload():
    """Switch to partload simulation tab."""
    ss.select = 'Partial load'


def reset2design():
    """Reset session state and switch to design simulation tab."""
    keys = list(ss.keys())
    for key in keys:
        ss.pop(key)
    ss.select = 'Configuration'


def info_df(label, refrigs):
    """Create Dataframe with info of chosen refrigerant."""
    df_refrig = pd.DataFrame(
        columns=['Typ', 'T_NBP', 'T_krit', 'p_krit', 'SK', 'ODP', 'GWP']
        )
    df_refrig.loc[label, 'Typ'] = refrigs[label]['type']
    df_refrig.loc[label, 'T_NBP'] = str(refrigs[label]['T_NBP'])
    df_refrig.loc[label, 'T_krit'] = str(refrigs[label]['T_crit'])
    df_refrig.loc[label, 'p_krit'] = str(refrigs[label]['p_crit'])
    df_refrig.loc[label, 'SK'] = refrigs[label]['ASHRAE34']
    df_refrig.loc[label, 'ODP'] = str(refrigs[label]['ODP'])
    df_refrig.loc[label, 'GWP'] = str(refrigs[label]['GWP100'])

    return df_refrig


def calc_limits(wf, prop, padding_rel, scale='lin'):
    """
    Calculate states diagram limits of given property.

    Parameters
    ----------

    wf : str
        Working fluid for which to filter heat pump simulation results.
    
    prop : str
        Fluid property to calculate limits for.

    padding_rel : float
        Padding from minimum and maximum value to axes limit in relation to
        full range between minimum and maximum.

    scale : str
        Either 'lin' or 'log'. Scale on with padding is applied. Defaults to
        'lin'.
    """
    if scale not in ['lin', 'log']:
        raise ValueError(
            f"Parameter 'scale' has to be either 'lin' or 'log'. '{scale}' is "
            + "not allowed."
            )

    wfmask = ss.hp.nw.results['Connection'][wf] == 1.0

    min_val = ss.hp.nw.results['Connection'].loc[wfmask, prop].min()
    max_val = ss.hp.nw.results['Connection'].loc[wfmask, prop].max()
    if scale == 'lin':
        delta_val = max_val - min_val
        ax_min_val = min_val - padding_rel * delta_val
        ax_max_val = max_val + padding_rel * delta_val
    elif scale == 'log':
        delta_val = np.log10(max_val) - np.log10(min_val)
        ax_min_val = 10 ** (np.log10(min_val) - padding_rel * delta_val)
        ax_max_val = 10 ** (np.log10(max_val) + padding_rel * delta_val)

    return ax_min_val, ax_max_val


src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

# %% MARK: Initialisation
refrigpath = os.path.join(src_path, 'refrigerants.json')
with open(refrigpath, 'r', encoding='utf-8') as file:
    refrigerants = json.load(file)

st.set_page_config(
    layout='wide',
    page_title='Heat pumps Dashboard',
    page_icon=os.path.join(src_path, 'img', 'page_icon_ZNES.png')
    )

is_dark = darkdetect.isDark()

# %% MARK: Sidebar

# with st.sidebar:
#     st.markdown("### Debug Settings")
#     debug_mode = st.radio(
#         "Debug Output Mode",
#         options=["None", "Streamlit", "Console"],
#         index=0,
#         key="debug_mode",
#     )


with st.sidebar: # Logo Here RG
    # Note: _dark.svg files have darker lines for light backgrounds
    # Regular .svg files have lighter lines for dark backgrounds
    if is_dark:
        logo = os.path.join(src_path, 'img', 'Logo_ZNES_mitUnisV2.svg')
    else:
        logo = os.path.join(src_path, 'img', 'Logo_ZNES_mitUnisV2_dark.svg')
    st.image(logo, use_container_width=True)

    mode = st.selectbox(
        "Selection mode",
        ["Start", "Configuration", "Partial load"],
        key="select",
        label_visibility="hidden",
    )

    st.markdown("""---""")

    # %% MARK: Design
    if mode == 'Configuration':
        ss.rerun_req = True
        st.header('Configuration of the Heat pump')

        with st.expander("H E A T &nbsp; P U M P &nbsp; T Y P E", expanded=True):
            base_topology = st.selectbox(
                'Basic topology',
                var.base_topologies,
                index=0, key='base_topology'
            )
            # Build a list of models for the selected base topology
            models = []
            for model, mdata in var.hp_models.items():
                if mdata['base_topology'] == base_topology:
                    if mdata['process_type'] != 'transcritical':
                        models.append(mdata['display_name'])

            model_name = st.selectbox('Heat pump model', models, index=0, key='model')

            process_type = st.radio(
                "Process type",
                options=("subcritical", "transcritical"),
                horizontal=True,
            )

            if process_type == 'transcritical':
                model_name = f'{model_name} | Transcritical'

            for model, mdata in var.hp_models.items():
                correct_base = mdata['base_topology'] == base_topology
                correct_model_name = mdata['display_name'] == model_name
                if correct_base and correct_model_name:
                    hp_model = mdata
                    hp_model_name = model
                    if 'trans' in hp_model_name:
                        hp_model_name_topology = hp_model_name.replace('_trans', '')
                    else:
                        hp_model_name_topology = hp_model_name
                    break

            # Clear old simulation results if model type changed
            if 'previous_model' in ss and ss.previous_model != hp_model_name:
                # Model changed - clear old results
                if 'hp' in ss:
                    del ss.hp
                if 'partload_char' in ss:
                    del ss.partload_char
            # Store current model for next comparison
            ss.previous_model = hp_model_name

            parampath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'models', 'input',
                f'params_hp_{hp_model_name}.json'
                ))
            with open(parampath, 'r', encoding='utf-8') as file:
                params = json.load(file)
        if hp_model['nr_ihx'] == 1:
            with st.expander("I N T E R N A L &nbsp; H E A T &nbsp; T R A N S F E R"):
                params["ihx"]["dT_sh"] = st.slider(
                    "Overheating/Hypothermia",
                    value=5,
                    min_value=0,
                    max_value=25,
                    format="%d°C",
                    key="dT_sh",
                )
        if hp_model['nr_ihx'] > 1:
            with st.expander("I N T E R N A L &nbsp; H E A T &nbsp; T R A N S F E R"):
                dT_ihx = {}
                for i in range(1, hp_model['nr_ihx']+1):
                    dT_ihx[i] = st.slider(
                        f"Nr. {i}: Overheating/Hypothermia",
                        value=5,
                        min_value=0,
                        max_value=25,
                        format="%d°C",
                        key=f"dT_ihx{i}",
                    )
                    params[f'ihx{i}']['dT_sh'] = dT_ihx[i]

        with st.expander('R E F R I G E R A N T'):
            if hp_model['nr_refrigs'] == 1:
                refrig_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig']:
                        refrig_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig']:
                        refrig_index = ridx
                        break

                refrig_label = st.selectbox(
                    '', refrigerants.keys(), index=refrig_index,
                    key='refrigerant'
                    )
                params['setup']['refrig'] = refrigerants[refrig_label]['CP']
                params['fluids']['wf'] = refrigerants[refrig_label]['CP']
                df_refrig = info_df(refrig_label, refrigerants)

            elif hp_model['nr_refrigs'] == 2:
                refrig2_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig2']:
                        refrig2_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig2']:
                        refrig2_index = ridx
                        break

                refrig2_label = st.selectbox(
                    "Refrigerant (High temperature circuit)",
                    refrigerants.keys(),
                    index=refrig2_index,
                    key="refrigerant2",
                )
                params['setup']['refrig2'] = refrigerants[refrig2_label]['CP']
                params['fluids']['wf2'] = refrigerants[refrig2_label]['CP']
                df_refrig2 = info_df(refrig2_label, refrigerants)

                refrig1_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig1']:
                        refrig1_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig1']:
                        refrig1_index = ridx
                        break

                refrig1_label = st.selectbox(
                    "Refrigerant (Low temperature circuit)",
                    refrigerants.keys(),
                    index=refrig1_index,
                    key="refrigerant1",
                )
                params['setup']['refrig1'] = refrigerants[refrig1_label]['CP']
                params['fluids']['wf1'] = refrigerants[refrig1_label]['CP']
                df_refrig1 = info_df(refrig1_label, refrigerants)

        if hp_model['nr_refrigs'] == 1:
            T_crit = int(np.floor(refrigerants[refrig_label]['T_crit']))
            p_crit = int(np.floor(refrigerants[refrig_label]['p_crit']))
        elif hp_model['nr_refrigs'] == 2:
            T_crit = int(np.floor(refrigerants[refrig2_label]['T_crit']))
            p_crit = int(np.floor(refrigerants[refrig2_label]['p_crit']))

        ss.T_crit = T_crit
        ss.p_crit = p_crit

        if 'trans' in hp_model_name:
            with st.expander("T R A N S C R I T I C A L &nbsp; P R E S S U R E"):
                params["A0"]["p"] = st.slider(
                    "flow temperature",
                    min_value=ss.p_crit,
                    value=params["A0"]["p"],
                    max_value=300,
                    format="%d bar",
                    key="p_trans_out",
                )

        with st.expander('T H E R M A L &nbsp; R A T I N G'):
            params["cons"]["Q"] = st.number_input(
                "Value in MW", value=abs(params["cons"]["Q"] / 1e6), step=0.1, key="Q_N"
            )
            params['cons']['Q'] *= -1e6

        with st.expander('H E A T &nbsp; S O U R C E'):
            params['B1']['T'] = st.slider(
                'Flow temperature', min_value=0, max_value=T_crit,
                value=params['B1']['T'], format='%d°C', key='T_heatsource_ff'
                )
            params['B2']['T'] = st.slider(
                'Return temperature', min_value=0, max_value=T_crit,
                value=params['B2']['T'], format='%d°C', key='T_heatsource_bf'
                )

            invalid_temp_diff = params['B2']['T'] >= params['B1']['T']
            if invalid_temp_diff:
                st.error(
                    "The return temperature must be lower than the "
                    + "flow temperature."
                )

        # TODO: Aktuell wird T_mid im Modell als Mittelwert zwischen von Ver-
        #       dampfungs- und Kondensationstemperatur gebildet. An sich wäre
        #       es analytisch sicher interessant den Wert selbst festlegen zu
        #       können.
        # if hp_model['nr_refrigs'] == 2:
        #     with st.expander('Zwischenwärmeübertrager'):
        #         param['design']['T_mid'] = st.slider(
        #             'Mittlere Temperatur', min_value=0, max_value=T_crit,
        #             value=40, format='%d°C', key='T_mid'
        #             )

        with st.expander('H E A T &nbsp; S I N K'):
            T_max_sink = T_crit
            if 'trans' in hp_model_name:
                T_max_sink = 200  # °C -- Ad hoc value, maybe find better one

            params['C3']['T'] = st.slider(
                'Flow temperature', min_value=0, max_value=T_max_sink,
                value=params['C3']['T'], format='%d°C', key='T_consumer_ff'
            )
            params['C1']['T'] = st.slider(
                'Return temperature', min_value=0, max_value=T_max_sink,
                value=params['C1']['T'], format='%d°C', key='T_consumer_bf'
            )

            invalid_temp_diff = params['C1']['T'] >= params['C3']['T']
            if invalid_temp_diff:
                st.error(
                    "The return temperature must be lower than the "
                    + "flow temperature."
                )
            invalid_temp_diff = params['C1']['T'] <= params['B1']['T']
            if invalid_temp_diff:
                st.error(
                    "The temperature of the heat sink must be higher than "
                    + "the heat source."
                )

        with st.expander("C O M P R E S S O R"):
            if hp_model['comp_var'] is None and hp_model['nr_refrigs'] == 1:
                params['comp']['eta_s'] = st.slider(
                    'Efficiency $\eta_s$', min_value=0, max_value=100, step=1,
                    value=int(params['comp']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is not None and hp_model['nr_refrigs'] == 1:
                params['comp1']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['comp2']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['comp2']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is None and hp_model['nr_refrigs'] == 2:
                params['HT_comp']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,HTK}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,NTK}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is not None and hp_model['nr_refrigs'] == 2:
                params['HT_comp1']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,HTK,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['HT_comp2']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,HTK,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp2']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp1']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,NTK,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp2']['eta_s'] = st.slider(
                    'Efficiency $\eta_{s,NTK,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp2']['eta_s']*100), format='%d%%'
                    ) / 100

        with st.expander("E N V. &nbsp; C O N D I T I O N S (exergy)"):
            params['ambient']['T'] = st.slider(
                'Temperature', min_value=1, max_value=45, step=1,
                value=params['ambient']['T'], format='%d°C', key='T_env'
                )
            params['ambient']['p'] = st.number_input(
                'Pressure in bars', value=float(params['ambient']['p']), step=0.01,
                format='%.4f', key='p_env'
                )

        with st.expander("C O S T &nbsp; P A R A M E T E R S"):
            costcalcparams = {}

            cepcipath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'models', 'input', 'CEPCI.json'
                ))
            with open(cepcipath, 'r', encoding='utf-8') as file:
                cepci = json.load(file)

            costcalcparams["current_year"] = st.selectbox(
                "Year of cost calculation",
                options=sorted(list(cepci.keys()), reverse=True),
                key="current_year",
            )

            costcalcparams["k_evap"] = st.slider(
                "Heat transfer coefficient (evaporation)",
                min_value=0,
                max_value=5000,
                step=10,
                value=1500,
                format="%d W/m²K",
                key="k_evap",
            )

            costcalcparams["k_cond"] = st.slider(
                "Heat transfer coefficient (condensation)",
                min_value=0,
                max_value=5000,
                step=10,
                value=3500,
                format="%d W/m²K",
                key="k_cond",
            )

            if 'trans' in hp_model_name:
                costcalcparams["k_trans"] = st.slider(
                    "Heat transfer coefficient (transcritical)",
                    min_value=0,
                    max_value=1000,
                    step=5,
                    value=60,
                    format="%d W/m²K",
                    key="k_trans",
                )

            costcalcparams["k_misc"] = st.slider(
                "Thermal transmittance coefficient (other)",
                min_value=0,
                max_value=1000,
                step=5,
                value=50,
                format="%d W/m²K",
                key="k_misc",
            )

            costcalcparams["residence_time"] = st.slider(
                "Flash tank residence time",
                min_value=0,
                max_value=60,
                step=1,
                value=10,
                format="%d s",
                key="residence_time",
            )

        ss.hp_params = params

        run_sim = st.button('🧮 Run Configuration')
        # run_sim = True
    # autorun = st.checkbox('AutoRun Simulation', value=True)

    # %% MARK: Offdesign
    if mode == 'Partial load' and 'hp' in ss:
        params = ss.hp_params
        st.header('Partial load Heat pump simulation')

        with st.expander('Partial load'):
            (
                params["offdesign"]["partload_min"],
                params["offdesign"]["partload_max"],
            ) = st.slider(
                "Related to nominal mass flow",
                min_value=0,
                max_value=120,
                step=5,
                value=(30, 100),
                format="%d%%",
                key="pl_slider",
            )

            params['offdesign']['partload_min'] /= 100
            params['offdesign']['partload_max'] /= 100

            params['offdesign']['partload_steps'] = int(np.ceil(
                    (params['offdesign']['partload_max']
                     - params['offdesign']['partload_min'])
                    / 0.1
                    ) + 1)

        with st.expander('Heat Source'):
            type_hs = st.radio(
                '', ('Constant', 'Variabel'), index=1, horizontal=True,
                key='temp_hs'
                )
            if type_hs == 'Constant':
                params['offdesign']['T_hs_ff_start'] = (
                    ss.hp.params['B1']['T']
                    )
                params['offdesign']['T_hs_ff_end'] = (
                    params['offdesign']['T_hs_ff_start'] + 1
                    )
                params['offdesign']['T_hs_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_hs_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_hs == 'Variabel':
                params['offdesign']['T_hs_ff_start'] = st.slider(
                    'Starting temperature',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['B1']['T']
                        - 5
                        ),
                    format='%d°C', key='T_hs_ff_start_slider'
                    )
                params['offdesign']['T_hs_ff_end'] = st.slider(
                    'Ending temperature',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['B1']['T']
                        + 5
                        ),
                    format='%d°C', key='T_hs_ff_end_slider'
                    )
                params['offdesign']['T_hs_ff_steps'] = int(np.ceil(
                    (params['offdesign']['T_hs_ff_end']
                     - params['offdesign']['T_hs_ff_start'])
                    / 3
                    ) + 1)

        with st.expander('Heat Sink'):
            type_cons = st.radio(
                '', ('Constant', 'Variabel'), index=1, horizontal=True,
                key='temp_cons'
                )
            if type_cons == 'Constant':
                params['offdesign']['T_cons_ff_start'] = (
                    ss.hp.params['C3']['T']
                    )
                params['offdesign']['T_cons_ff_end'] = (
                    params['offdesign']['T_cons_ff_start'] + 1
                    )
                params['offdesign']['T_cons_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_cons_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_cons == 'Variabel':
                params['offdesign']['T_cons_ff_start'] = st.slider(
                    'Starting temperature',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['C3']['T']
                        - 10
                        ),
                    format='%d°C', key='T_cons_ff_start_slider'
                    )
                params['offdesign']['T_cons_ff_end'] = st.slider(
                    'Ending temperature',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['C3']['T']
                        + 10
                        ),
                    format='%d°C', key='T_cons_ff_end_slider'
                    )
                params['offdesign']['T_cons_ff_steps'] = int(np.ceil(
                    (params['offdesign']['T_cons_ff_end']
                     - params['offdesign']['T_cons_ff_start'])
                    / 1
                    ) + 1)

        ss.hp_params = params
        run_pl_sim = st.button('🧮 Partial load Simulation')

# %% MARK: Main Content
st.title('*heatpumps*')

if mode == 'Start':
    # %% MARK: Landing Page
    st.write(
        """Of the heat pump simulator * heat pump * is a powerful simulation software for analyzing and evaluating heat pumps. With this dashboard, a variety of complex thermodynamic system models can be controlled using numerical methods using a simple surface.Partial loading.[TESPY] (https://github.com/oemof/tespy)
        - Parameterisation and result visualisation using a [Streamlit](https://github.com/streamlit/streamlit) Dashboard
        - Circuit topologies commonly used in industry, research and development
        - Sub- and transcritical processes
        - Wide range of working media due to the integration of [CoolProp](https://github.com/CoolProp/CoolProp)
        """
    )

    # Create two columns for spacing
    col1, col2 = st.columns([1, 1])  # Adjust ratio for spacing

    with col1:
        st.button("Start", on_click=switch2design)

    with col2:
        st.button("Exit", on_click=exit_app)

    # st.button('Start', on_click=switch2design)

    st.markdown("""---""")

    with st.expander('Software used'):
        st.info(
            """
            #### Software used:
            The open source software TESPy is used to create models and calculate
            simulations. In addition, a number of other Python packages are used 
            for data processing, preparation and visualization.

            ---

            #### TESPy:

            TESPy (Thermal Engineering Systems in Python) is a
            powerful simulation tool for thermal process engineering, for example
            for power plants, district heating systems or heat pumps. With the 
            TESPy package it is possible to design systems and simulate stationary 
            operation. The partial load behavior can then be determined based on 
            the underlying characteristics for each component of the system. 
            The component-based structure in combination with the solution 
            method offers a very high degree of flexibility with regard to 
            the system topology and parameterization. Further information 
            on TESPy can be found in its 
            [online documentation](https://tespy.readthedocs.io) in English.

            #### Auxiliary modules:

            - [Streamlit](https://docs.streamlit.io) (Graphische Oberfläche)
            - [NumPy](https://numpy.org) (Datenverarbeitung)
            - [pandas](https://pandas.pydata.org) (Datenverarbeitung)
            - [SciPy](https://scipy.org/) (Interpolation)
            - [scikit-learn](https://scikit-learn.org) (Regression)
            - [Matplotlib](https://matplotlib.org) (Datenvisualisierung)
            - [FluProDia](https://fluprodia.readthedocs.io) (Datenvisualisierung)
            - [CoolProp](http://www.coolprop.org) (Stoffdaten)
            """
        )

    with st.expander('Disclaimer'):
        st.warning(
            """
            #### Simulations Results:

            Numerical simulations are calculations using suitable iteration methods in
            relation to the specified and set boundary conditions and parameters. 
            In individual cases, it is not possible to take all possible influences into 
            account, so that deviations from empirical values ​​from practical applications 
            can arise and must be taken into account in the evaluation. The results 
            provide sufficient to precise information about the basic behavior, the COP
            and state variables in the individual components of the heat pump. 
            However, all information and results are without guarantee.
            """
        )

    with st.expander('Copyright'):

        st.success(
            """
            #### Software license
            MIT License

            Copyright © 2023 Jonas Freißmann and Malte Fritz

            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:

            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.

            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.
            """
        )


if mode == 'Configuration':
    # %% MARK: Design Simulation
    if not run_sim:
        # %% Topology & Refrigerant
        col_left, col_right = st.columns([1, 4])

        with col_left:
            st.subheader('Topology')

            # Note: _dark.svg files have darker lines for light backgrounds
            # Regular .svg files have lighter lines for dark backgrounds
            if is_dark:
                top_file = os.path.join(
                    src_path, 'img', 'topologies', f'hp_{hp_model_name_topology}.svg'
                    )
                st.image(top_file)
            else:
                try:
                    top_file = os.path.join(
                        src_path, 'img', 'topologies',
                        f'hp_{hp_model_name_topology}_dark.svg'
                        )
                    st.image(top_file)
                except:
                    top_file = os.path.join(
                        src_path, 'img', 'topologies', f'hp_{hp_model_name_topology}.svg'
                        )
                    st.image(top_file)

        with col_right:
            st.subheader('Refrigerant')

            if hp_model['nr_refrigs'] == 1:
                st.dataframe(df_refrig, use_container_width=True)
            elif hp_model['nr_refrigs'] == 2:
                st.markdown("#### High temperature circuit")
                st.dataframe(df_refrig2, use_container_width=True)
                st.markdown("#### Low temperature circuit")
                st.dataframe(df_refrig1, use_container_width=True)

            st.write("""
                All fabric data and classifications from [Coolprop] (http://www.coolprop.org) or [Arpagaus et al. (2018)] (https://doi.org/10.1016/J.ENERGY.2018.03.166)
                """
            )

        with st.expander('Instructions'):
            st.info(
                """
                #### Instructions

                You are on theConfiguration interface to simulate a heat pump. 
                In addition to the dimensioning of the pmp and selecting the refrigerant 
                to be used, various central parameters of the cycle process must be specified 
                on the sidebar on the left. 

                These include, for example, the temperatures of the heat source and sink, and 
                the associated network pressures. In addition, an internal heat exchanger 
                can optionally be added. The resulting superheat of the evaporated refrigerant 
                must also be specified. Once the simulation Configuration has been successfully
                completed, the generated results are graphically processed and quantified in state diagrams. 

                The central variables such as the coefficient of performance (COP) and the
                relevant heat flows and power are tabulated. In addition, the thermodynamic state
                variables in all process steps are listed in tabular form. After the simulation
                is completed, a button appears, offering optional partial load settings. This can also
                be done via the dropdown menu in the sidebar. Information on how to carry out the 
                partial load simulations can be found on the home page of this interface.
                """
            )

    if run_sim:
        # %% Run Design Simulation
        with st.spinner('Simulation underway ...'):
            try:
                ss.hp = run_design(hp_model_name, params)
                sim_succeded = True
                st.success(
                    "The simulation of the heat pump Configuration was successful."
                )
            except ValueError as e:
                sim_succeded = False
                print(f'ValueError: {e}')
                st.error(
                    "When simulating the heat pump, the following "
                    + "Error occurred. Please correct the "
                    + f'input parameters and try again.\n\n"{e}"'
                )

    # %% MARK: Results
    # Show results if simulation just succeeded OR if there's already a heat pump in session state
    if 'hp' in ss:
        with st.spinner("Results ..."):

            stateconfigpath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'models', 'input',
                'state_diagram_config.json'
                ))
            with open(stateconfigpath, 'r', encoding='utf-8') as file:
                config = json.load(file)
            if hp_model['nr_refrigs'] == 1:
                if ss.hp.params['setup']['refrig'] in config:
                    state_props = config[
                        ss.hp.params['setup']['refrig']
                        ]
                else:
                    state_props = config['MISC']
            if hp_model['nr_refrigs'] == 2:
                if ss.hp.params['setup']['refrig1'] in config:
                    state_props1 = config[
                        ss.hp.params['setup']['refrig1']
                        ]
                else:
                    state_props1 = config['MISC']
                if ss.hp.params['setup']['refrig2'] in config:
                    state_props2 = config[
                        ss.hp.params['setup']['refrig2']
                        ]
                else:
                    state_props2 = config['MISC']

            st.header("Configuration results")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric('COP', round(ss.hp.cop, 2))
            Q_dot_ab = abs(
                ss.hp.buses['heat output'].P.val / 1e6
                )
            col2.metric('Q_dot_ab', f"{Q_dot_ab:.2f} MW")
            col3.metric(
                'P_zu',
                f"{ss.hp.buses['power input'].P.val/1e6:.2f} MW"
                )
            Q_dot_zu = abs(
                ss.hp.comps['evap'].Q.val/1e6
                )
            col4.metric('Q_dot_zu', f'{Q_dot_zu:.2f} MW')

            with st.expander(
                "T O P O L O G Y &nbsp; & &nbsp; R E F R I G E R A N T"
            ):
                # %% Topology & Refrigerant
                col_left, col_right = st.columns([1, 4])

                with col_left:
                    st.subheader('Topology')

                    # Note: _dark.svg files have darker lines for light backgrounds
                    # Regular .svg files have lighter lines for dark backgrounds
                    top_file = os.path.join(
                        src_path, 'img', 'topologies',
                        f'hp_{hp_model_name_topology}_label.svg'
                        )
                    if not is_dark:
                        top_file_dark = os.path.join(
                            src_path, 'img', 'topologies',
                            f'hp_{hp_model_name_topology}_label_dark.svg'
                            )
                        if os.path.exists(top_file_dark):
                            top_file = top_file_dark

                    st.image(top_file)

                with col_right:
                    st.subheader('Refrigerant')

                    if hp_model['nr_refrigs'] == 1:
                        st.dataframe(df_refrig, use_container_width=True)
                    elif hp_model['nr_refrigs'] == 2:
                        st.markdown("#### High temperature circuit")
                        st.dataframe(df_refrig2, use_container_width=True)
                        st.markdown("#### Low temperature circuit")
                        st.dataframe(df_refrig1, use_container_width=True)

                    st.write("""
                             All fabric data and classifications from [Coolprop] (http://www.coolprop.org) or [Arpagaus et al. (2018)] (https://doi.org/10.1016/J.ENERGY.2018.03.166)
                            """
                            )

            with st.expander('S T A T E &nbsp; D I A G R A M S'):
                # %% State Diagrams
                col_left, _, col_right = st.columns([0.495, 0.01, 0.495])
                _, slider_left, _, slider_right, _ = (
                    st.columns([0.5, 8, 1, 8, 0.5])
                    )

                if is_dark:
                    state_diagram_style = 'dark'
                else:
                    state_diagram_style = 'light'

                with col_left:
                    # %% Log(p)-h-Diagram
                    st.subheader('Log(p)-h-Diagram')
                    if hp_model['nr_refrigs'] == 1:
                        xmin, xmax = calc_limits(
                            wf=ss.hp.wf, prop='h', padding_rel=0.35
                            )
                        ymin, ymax = calc_limits(
                            wf=ss.hp.wf, prop='p', padding_rel=0.25,
                            scale='log'
                            )

                        diagram = ss.hp.generate_state_diagram(
                            diagram_type='logph',
                            figsize=(12, 7.5),
                            xlims=(xmin, xmax), ylims=(ymin, ymax),
                            style=state_diagram_style,
                            return_diagram=True, display_info=False,
                            open_file=False, savefig=False
                            )
                        st.pyplot(diagram.fig)

                    elif hp_model['nr_refrigs'] == 2:
                        xmin1, xmax1 = calc_limits(
                            wf=ss.hp.wf1, prop='h', padding_rel=0.35
                            )
                        ymin1, ymax1 = calc_limits(
                            wf=ss.hp.wf1, prop='p', padding_rel=0.25,
                            scale='log'
                            )

                        xmin2, xmax2 = calc_limits(
                            wf=ss.hp.wf2, prop='h', padding_rel=0.35
                            )
                        ymin2, ymax2 = calc_limits(
                            wf=ss.hp.wf2, prop='p', padding_rel=0.25,
                            scale='log'
                            )

                        diagram1, diagram2 = ss.hp.generate_state_diagram(
                            diagram_type='logph',
                            figsize=(12, 7.5),
                            xlims=((xmin1, xmax1), (xmin2, xmax2)),
                            ylims=((ymin1, ymax1), (ymin2, ymax2)),
                            style=state_diagram_style,
                            return_diagram=True, display_info=False,
                            savefig=False, open_file=False
                            )
                        st.pyplot(diagram1.fig)
                        st.pyplot(diagram2.fig)

                with col_right:
                    # %% T-s-Diagram
                    st.subheader('T-s-Diagram')
                    if hp_model['nr_refrigs'] == 1:
                        xmin, xmax = calc_limits(
                            wf=ss.hp.wf, prop='s', padding_rel=0.35
                            )
                        ymin, ymax = calc_limits(
                            wf=ss.hp.wf, prop='T', padding_rel=0.25
                            )

                        diagram = ss.hp.generate_state_diagram(
                            diagram_type='Ts',
                            figsize=(12, 7.5),
                            xlims=(xmin, xmax), ylims=(ymin, ymax),
                            style=state_diagram_style,
                            return_diagram=True, display_info=False,
                            open_file=False, savefig=False
                            )
                        st.pyplot(diagram.fig)

                    elif hp_model['nr_refrigs'] == 2:
                        xmin1, xmax1 = calc_limits(
                            wf=ss.hp.wf1, prop='s', padding_rel=0.35
                            )
                        ymin1, ymax1 = calc_limits(
                            wf=ss.hp.wf1, prop='T', padding_rel=0.25
                            )

                        xmin2, xmax2 = calc_limits(
                            wf=ss.hp.wf2, prop='s', padding_rel=0.35
                            )
                        ymin2, ymax2 = calc_limits(
                            wf=ss.hp.wf2, prop='T', padding_rel=0.25
                            )

                        diagram1, diagram2 = ss.hp.generate_state_diagram(
                            diagram_type='Ts',
                            figsize=(12, 7.5),
                            xlims=((xmin1, xmax1), (xmin2, xmax2)),
                            ylims=((ymin1, ymax1), (ymin2, ymax2)),
                            style=state_diagram_style,
                            return_diagram=True, display_info=False,
                            savefig=False, open_file=False
                            )
                        st.pyplot(diagram1.fig)
                        st.pyplot(diagram2.fig)

            with st.expander('S T A T E &nbsp; V A R I A B L E S'):
                # %% State Quantities
                state_quantities = (
                    ss.hp.nw.results['Connection'].copy()
                    )
                state_quantities = state_quantities.loc[:, ~state_quantities.columns.str.contains('_unit', case=False, regex=False)]
                try:
                    state_quantities['water'] = (
                        state_quantities['water'] == 1.0
                        )
                except KeyError:
                    state_quantities['H2O'] = (
                        state_quantities['H2O'] == 1.0
                        )
                if hp_model['nr_refrigs'] == 1:
                    refrig = ss.hp.params['setup']['refrig']
                    state_quantities[refrig] = (
                        state_quantities[refrig] == 1.0
                        )
                elif hp_model['nr_refrigs'] == 2:
                    refrig1 = ss.hp.params['setup']['refrig1']
                    state_quantities[refrig1] = (
                        state_quantities[refrig1] == 1.0
                        )
                    refrig2 = ss.hp.params['setup']['refrig2']
                    state_quantities[refrig2] = (
                        state_quantities[refrig2] == 1.0
                        )
                if 'Td_bp' in state_quantities.columns:
                    del state_quantities['Td_bp']
                for col in state_quantities.columns:
                    if state_quantities[col].dtype == np.float64:
                        state_quantities[col] = state_quantities[col].apply(
                            lambda x: f'{x:.5}'
                            )
                state_quantities['x'] = state_quantities['x'].apply(
                    lambda x: '-' if float(x) < 0 else x
                    )
                state_quantities.rename(
                    columns={
                        'm': 'm in kg/s',
                        'p': 'p in bar',
                        'h': 'h in kJ/kg',
                        'T': 'T in °C',
                        'v': 'v in m³/kg',
                        'vol': 'vol in m³/s',
                        's': 's in kJ/(kgK)'
                        },
                    inplace=True)
                st.dataframe(
                    data=state_quantities, use_container_width=True
                    )

            with st.expander("E C O N O M I C &nbsp; E V A L U A T I O N"):
                # %% Eco Results
                ss.hp.calc_cost(
                    ref_year='2013', **costcalcparams
                    )

                col1, col2 = st.columns(2)
                invest_total = ss.hp.cost_total
                col1.metric("Total investment costs", f"{invest_total:,.0f} €")
                inv_sepc = (
                    invest_total
                    / abs(ss.hp.params["cons"]["Q"]/1e6)
                    )
                col2.metric("specific investment costs", f"{inv_sepc:,.0f} €/MW")
                costdata = pd.DataFrame({
                    k: [round(v, 2)]
                    for k, v in ss.hp.cost.items()
                    })
                st.dataframe(costdata, use_container_width=True, hide_index=True)

                st.write(""" Methodology for the calculation of the costs analogous to [Kosmadakis et al. (2020)] (https://doi.org/10.1016/j.enconman.2020.113488), based on [Bejan et al.(1995)] (https://www.wiley.com/en-us/thermal+Design+And+optimization-P-9780471584674).""")

            with st.expander("E X E R G Y &nbsp; A S S E S S M E N T"):
                # %% Exergy Analysis
                st.header("results of the exergy analysis")

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric(
                    'Epsilon',
                    f'{ss.hp.ean.network_data.epsilon*1e2:.2f} %'
                    )
                col2.metric(
                    'E_F',
                    f'{(ss.hp.ean.network_data.E_F)/1e6:.2f} MW'
                    )
                col3.metric(
                    'E_P',
                    f'{(ss.hp.ean.network_data.E_P)/1e6:.2f} MW'
                    )
                col4.metric(
                    'E_D',
                    f'{(ss.hp.ean.network_data.E_D)/1e6:.2f} MW'
                    )
                col5.metric(
                    'E_L',
                    f'{(ss.hp.ean.network_data.E_L)/1e3:.2f} KW'
                    )

                st.subheader("Results by component")
                exergy_component_result = (
                    ss.hp.ean.component_data.copy()
                    )
                exergy_component_result = exergy_component_result.drop(
                    'group', axis=1
                    )
                exergy_component_result.dropna(subset=['E_F'], inplace=True)
                for col in ['E_F', 'E_P', 'E_D']:
                    exergy_component_result[col] = (
                        exergy_component_result[col].round(2)
                        )
                for col in ['epsilon', 'y_Dk', 'y*_Dk']:
                    exergy_component_result[col] = (
                        exergy_component_result[col].round(4)
                        )
                exergy_component_result.rename(
                    columns={
                        'E_F': 'E_F in W',
                        'E_P': 'E_P in W',
                        'E_D': 'E_D in W',
                    },
                    inplace=True)
                st.dataframe(
                    data=exergy_component_result, use_container_width=True
                    )

                col6, _, col7 = st.columns([0.495, 0.01, 0.495])
                with col6:
                    st.subheader('Sankey Diagram')
                    diagram_placeholder_sankey = st.empty()

                    diagram_sankey = ss.hp.generate_sankey_diagram()
                    diagram_placeholder_sankey.plotly_chart(
                        diagram_sankey, use_container_width=True
                        )
                # RRG >>>
                with col7:
                    st.subheader('Waterfall Diagram')
                    diagram_placeholder_waterfall = st.empty()

                    # if run_sim:
                    #     debug_refrigerant_state(mode=debug_mode)

                    diagram_waterfall = ss.hp.generate_waterfall_diagram()

                    if isinstance(diagram_waterfall, matplotlib.figure.Figure):
                        diagram_placeholder_waterfall.pyplot(diagram_waterfall, use_container_width=True)
                    elif diagram_waterfall is None:
                        st.warning("⚠️ Waterfall diagram not generated — figure is `None`.")
                    else:
                        st.warning("⚠️ Waterfall diagram could not be rendered (invalid figure type).")

                # RG <<<
                # Original >>>
                # with col7:
                #     st.subheader('Waterfall Diagram')
                #     diagram_placeholder_waterfall = st.empty()
                #     if run_sim:
                #         # Debug Just before plotting state diagrams, if requested
                #         debug_refrigerant_state(mode=debug_mode)

                #     diagram_waterfall = ss.hp.generate_waterfall_diagram()
                #     diagram_placeholder_waterfall.pyplot(
                #                         diagram_waterfall, use_container_width=True
                #                         )
                # Original <<<

                st.write(
                    """ Definitions and Methodology of Exergie Analysis based on [Morosuk and Tsatsaronis (2019)] (https://doi.org/10.1016/J.ENERGY.2018.10.090), whose implementation in Tuty describes in [Witte and Hofmann et al.(2022)] (https://doi.org/10.3390/en15114087)
                    and didactically prepared in [Witte, Freißmann und Fritz (2023)](https://fwitte.github.io/TESPy_teaching_exergy/).
                    """
                )

            # Save & Share Report button
            st.divider()
            col_report, col_partload = st.columns([1, 1])

            with col_report:
                if st.button('📤 Save & Share Report', use_container_width=True):
                    try:
                        # Extract simulation data
                        with st.spinner('Extracting simulation data...'):
                            report_data = extract_report_data(ss.hp)

                        st.success("✅ Data extracted successfully")

                        # Generate report ID
                        report_id = str(uuid.uuid4())

                        # Prepare metadata
                        metadata = {
                            "report_id": report_id,
                            "created_at": datetime.utcnow().isoformat() + "Z",
                            "model_name": ss.hp.params.get('setup', {}).get('name', 'Heat Pump Model'),
                            "topology": ss.hp.params.get('setup', {}).get('type', 'Unknown'),
                            "refrigerant": ss.hp.params.get('setup', {}).get('refrig', 'Unknown')
                        }

                        # Call API to save report
                        with st.spinner('Uploading to cloud storage...'):
                            api_url = "https://heatpump-api-bo6wip2gyq-nw.a.run.app"
                            response = httpx.post(
                                f"{api_url}/api/v1/reports/save",
                                json={
                                    "simulation_data": report_data,
                                    "metadata": metadata
                                },
                                timeout=60.0  # Increased timeout
                            )

                        if response.status_code == 201:
                            data = response.json()
                            st.success("✅ Report saved successfully!")

                            # Display shareable URL
                            st.markdown("### 🔗 Shareable URL")
                            st.code(data['signed_url'], language="text")

                            st.info(f"📅 This link will remain accessible. You can share it with others to view your simulation results.")

                            # Display report ID for reference
                            with st.expander("📋 Report Details"):
                                st.text(f"Report ID: {data['report_id']}")
                                st.text(f"Storage: {data['storage_url']}")
                        else:
                            st.error(f"❌ Failed to save report (HTTP {response.status_code})")
                            st.code(response.text)

                    except Exception as e:
                        st.error(f"❌ Error saving report: {str(e)}")
                        st.exception(e)

            with col_partload:
                st.button('Partial load Simulation', on_click=switch2partload, use_container_width=True)

            st.info(
                'To calculate the partial load, press "Partial load simulation".'
            )

if mode == 'Partial load':
    # %% MARK: Offdesign Simulation
    st.header("Operating characteristics")

    if 'hp' not in ss:
        st.warning(
            """
            To carry out a partial load simulation, a 
            heat pump must first be designed. Please first switch to the 
            'Configuration' mode.
            """
        )
    else:
        if not run_pl_sim and 'partload_char' not in ss:
            # %% Landing Page
            st.write("'Parameterisation of the partial load calculation: + percentage part load + area of ​​the source temperature + area of ​​the lowering temperature' '')")

        if run_pl_sim:
            # %% Run Offdesign Simulation
            with st.spinner('Partial load simulation running ... may take a while'):
                ss.hp, ss.partload_char = (
                    run_partload(ss.hp)
                    )
                # ss.partload_char = pd.read_csv(
                #     'partload_char.csv', index_col=[0, 1, 2], sep=';'
                #     )
                st.success(
                    "The simulation of the heat pump characteristics was successful"
                )

        if run_pl_sim or 'partload_char' in ss:
            # %% Results
            with st.spinner('Results will be charted ...'):

                with st.expander('Diagram', expanded=True):
                    col_left, col_right = st.columns(2)

                    with col_left:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='COP',
                            cmap='plasma', return_fig_ax=True
                            )
                        pl_cop_placeholder = st.empty()

                        if type_hs == 'Constant':
                            T_select_cop = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                                )
                        elif type_hs == 'Variabel':
                            T_hs_min = ss.hp.params['offdesign']['T_hs_ff_start']
                            T_hs_max = ss.hp.params['offdesign']['T_hs_ff_end']
                            T_select_cop = st.slider(
                                "Source temperature",
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_cop_slider",
                            )

                        pl_cop_placeholder.pyplot(figs[T_select_cop])

                    with col_right:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='T_cons_ff',
                            cmap='plasma', return_fig_ax=True
                            )
                        pl_T_cons_ff_placeholder = st.empty()

                        if type_hs == 'Constant':
                            T_select_T_cons_ff = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                                )
                        elif type_hs == 'Variabel':
                            T_select_T_cons_ff = st.slider(
                                "Source temperature",
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_T_cons_ff_slider",
                            )
                        pl_T_cons_ff_placeholder.pyplot(figs[T_select_T_cons_ff])

                with st.expander("Partial load Exergy analysis", expanded=True):

                    col_left_1, col_right_1 = st.columns(2)

                    with col_left_1:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='epsilon',
                            cmap='plasma', return_fig_ax=True
                        )
                        pl_epsilon_placeholder = st.empty()

                        if type_hs == 'Constant':
                            T_select_epsilon = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                            )
                        elif type_hs == 'Variabel':
                            T_hs_min = ss.hp.params['offdesign']['T_hs_ff_start']
                            T_hs_max = ss.hp.params['offdesign']['T_hs_ff_end']
                            T_select_epsilon = st.slider(
                                "Source temperature",
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_epsilon_slider",
                            )

                        pl_epsilon_placeholder.pyplot(figs[T_select_epsilon])

                st.button("Designing a new heat pump", on_click=reset2design)

# if __name__ == "__main__":
#     ss.hp = run_design(hp_model_name, params)
#     debug_refrigerant_state(mode="console")
