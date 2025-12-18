"""
Centralized parameter descriptions for heat pump simulation reports.

This module provides human-readable descriptions for all input parameters
used in heat pump simulations. These descriptions are displayed in the
HTML report's Input Parameters section.

To add or modify descriptions, update the PARAMETER_DESCRIPTIONS dictionary below.
"""

# Parameter descriptions dictionary
# Key: parameter name as stored in JSON (e.g., 'T_source_in', 'eta_s')
# Value: Human-readable description
PARAMETER_DESCRIPTIONS = {
    # Temperature Parameters
    'T': 'Temperature',
    'T_source_in': 'Heat source inlet temperature',
    'T_source_out': 'Heat source outlet temperature',
    'T_sink_in': 'Heat sink inlet temperature',
    'T_sink_out': 'Heat sink outlet temperature',
    'T_amb': 'Ambient reference temperature for exergy calculations',
    'T_mid': 'Intermediate temperature (cascade systems)',

    # Pressure Parameters
    'p': 'Pressure',
    'p_evap': 'Evaporator pressure',
    'p_cond': 'Condenser pressure',
    'p_ihx_hot_in': 'Internal heat exchanger hot side inlet pressure',
    'p_ihx_cold_in': 'Internal heat exchanger cold side inlet pressure',

    # Pressure Ratios
    'pr': 'Pressure ratio',
    'pr_cond_hot': 'Condenser hot-side pressure ratio (pressure drop)',
    'pr_cond_cold': 'Condenser cold-side pressure ratio (pressure drop)',
    'pr_evap_hot': 'Evaporator hot-side pressure ratio (pressure drop)',
    'pr_evap_cold': 'Evaporator cold-side pressure ratio (pressure drop)',
    'pr_ihx_hot': 'IHX hot-side pressure ratio (pressure drop)',
    'pr_ihx_cold': 'IHX cold-side pressure ratio (pressure drop)',

    # Temperature Differences
    'deltaT_superheat': 'Superheating temperature difference at evaporator outlet',
    'deltaT_subcool': 'Subcooling temperature difference at condenser outlet',
    'ttd_u': 'Upper terminal temperature difference',
    'ttd_l': 'Lower terminal temperature difference',

    # Compressor Parameters
    'eta_s': 'Isentropic compressor efficiency',
    'eta_mech': 'Mechanical efficiency',
    'eta_s_1': 'Isentropic efficiency (1st stage compressor)',
    'eta_s_2': 'Isentropic efficiency (2nd stage compressor)',

    # Heat Transfer Parameters
    'Q': 'Heat transfer rate / Thermal capacity',
    'heat_output': 'Target heat output (thermal rating)',
    'heat_input': 'Heat input from source',
    'power_input': 'Compressor power consumption',

    # Mass Flow
    'm': 'Mass flow rate',

    # Fluid/Setup Parameters
    'refrigerant': 'Working fluid (refrigerant) for the cycle',
    'refrig': 'Refrigerant name',
    'refrig1': 'Low temperature circuit refrigerant (cascade)',
    'refrig2': 'High temperature circuit refrigerant (cascade)',
    'model_type': 'Heat pump topology type',
    'name': 'Model name',
    'type': 'Model type identifier',

    # Configuration Parameters
    'nr_ihx_stages': 'Number of internal heat exchanger stages',
    'nr_refrigerant_streams': 'Number of parallel refrigerant streams',
    'nr_refrigs': 'Number of refrigerant circuits',
    'econ_type': 'Economizer type (closed/open)',
    'intercooler': 'Intercooler enabled/disabled',
    'transcritical': 'Transcritical cycle operation mode',
    'comp_var': 'Compressor variant configuration',

    # Connection point identifiers (B=Source, C=Sink, A=Refrigerant)
    'B1': 'Heat source flow connection',
    'B2': 'Heat source return connection',
    'C1': 'Heat sink return connection',
    'C3': 'Heat sink flow connection',
    'A0': 'Refrigerant high pressure point',

    # Economic Parameters
    'cost_total': 'Total investment cost',
    'specific_cost': 'Specific investment cost per kW',
}


def get_description(param_name: str) -> str:
    """
    Get the description for a parameter name.

    Args:
        param_name: The parameter name (e.g., 'T_source_in', 'eta_s')

    Returns:
        Human-readable description, or empty string if not found
    """
    return PARAMETER_DESCRIPTIONS.get(param_name, '')


def get_all_descriptions() -> dict:
    """
    Get all parameter descriptions.

    Returns:
        Dictionary of parameter names to descriptions
    """
    return PARAMETER_DESCRIPTIONS.copy()
