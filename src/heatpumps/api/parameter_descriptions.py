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

    # Refrigerant Properties
    'Typ': 'Refrigerant category and typical use',
    'T_NBP': 'Normal boiling point - temperature at which the refrigerant boils under normal conditions',
    'T_krit': 'Critical temperature - maximum temperature where the refrigerant can still be liquid',
    'p_krit': 'Critical pressure - pressure where liquid and gas states merge',
    'SK': 'Safety classification - ASHRAE 34 rating for flammability and toxicity',
    'ODP': 'Ozone Depletion Potential - impact on the ozone layer (lower is better)',
    'GWP': 'Global Warming Potential - global warming impact compared to CO2',
    'GWP100': 'Global Warming Potential over 100 years',
    'ASHRAE34': 'ASHRAE Standard 34 safety classification',

    # Exergy Parameters
    'epsilon': 'Exergetic efficiency - ratio of product exergy to fuel exergy',
    'E_F': 'Fuel exergy - exergy supplied to the system',
    'E_P': 'Product exergy - useful exergy output from the system',
    'E_D': 'Exergy destruction - exergy lost due to irreversibilities',
    'E_L': 'Exergy loss - exergy lost to the environment',
    'y_Dk': 'Exergy destruction ratio - component exergy destruction relative to total',

    # Performance Metrics
    'COP': 'Coefficient of Performance - ratio of heat output to work input',
    'Q_dot_ab': 'Heat output rate - thermal power delivered to heat sink',
    'Q_dot_zu': 'Heat input rate - thermal power extracted from heat source',
    'P_zu': 'Power input - electrical power consumed by compressor',
}


# Glossary terms for reports - extracted from PARAMETER_DESCRIPTIONS
GLOSSARY_TERMS = {
    'COP': 'Coefficient of Performance - the ratio of heat output to work input, measuring heat pump efficiency',
    'Exergy': 'The maximum useful work obtainable from a system as it reaches equilibrium with its environment',
    'Epsilon (ε)': 'Exergetic efficiency - the ratio of product exergy to fuel exergy, indicating thermodynamic perfection',
    'E_F': 'Fuel Exergy - the exergy supplied to drive the heat pump (compressor work)',
    'E_P': 'Product Exergy - the useful exergy output (heat delivered at temperature above ambient)',
    'E_D': 'Exergy Destruction - exergy lost within components due to irreversibilities (friction, heat transfer across temperature differences)',
    'E_L': 'Exergy Loss - exergy transferred to the environment without useful purpose',
    'Isentropic Efficiency': 'Compressor efficiency comparing actual work to ideal (reversible) work for the same pressure ratio',
    'Superheat': 'Temperature increase of refrigerant vapor above its saturation temperature at a given pressure',
    'Subcooling': 'Temperature decrease of refrigerant liquid below its saturation temperature at a given pressure',
    'TTD (Terminal Temperature Difference)': 'Temperature difference between fluids at heat exchanger inlet or outlet',
    'Pressure Ratio': 'Ratio of discharge pressure to suction pressure across a compressor',
    'Critical Point': 'The temperature and pressure above which distinct liquid and gas phases do not exist',
    'ODP': 'Ozone Depletion Potential - environmental metric comparing ozone layer impact to R-11 (CFC-11 = 1.0)',
    'GWP': 'Global Warming Potential - environmental metric comparing greenhouse effect to CO2 over 100 years',
    'ASHRAE 34': 'Safety classification system for refrigerants (e.g., A1 = non-toxic/non-flammable, B2L = low toxicity/mildly flammable)',
    'Sankey Diagram': 'Flow diagram showing exergy flows through the system, with widths proportional to flow magnitude',
    'Waterfall Diagram': 'Chart showing cumulative exergy destruction from fuel to product exergy',
}


def get_glossary() -> dict:
    """
    Get glossary terms for display in reports.

    Returns:
        Dictionary of term names to descriptions
    """
    return GLOSSARY_TERMS.copy()


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
