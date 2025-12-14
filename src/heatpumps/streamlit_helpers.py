"""
Helper functions for Streamlit dashboard.

This module provides utilities for extracting and formatting
simulation data for reporting and API integration.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import math
import logging

logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """
    Recursively sanitize data structure for JSON serialization.

    Converts NaN, Infinity, and -Infinity to None (null in JSON).
    Handles nested dictionaries, lists, pandas Series, and numpy arrays.

    Args:
        obj: Any Python object to sanitize

    Returns:
        Sanitized object safe for JSON serialization
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, pd.Series):
        return sanitize_for_json(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict('records'))
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, (np.integer, np.floating)):
        return sanitize_for_json(obj.item())
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif pd.isna(obj):  # Catch pandas NA/NaT
        return None
    else:
        return obj


def extract_report_data(hp_object) -> Dict[str, Any]:
    """
    Extract complete simulation data from heat pump object for report generation.

    This function serializes all relevant simulation results into a JSON-compatible
    dictionary structure that includes:
    - Configuration results (COP, heat output, power, etc.)
    - Topology and refrigerant information
    - State variables (thermodynamic state points)
    - Economic evaluation (costs)
    - Exergy assessment (efficiency analysis)
    - Full parameters for reproducibility

    Args:
        hp_object: Heat pump model instance from simulation

    Returns:
        Dictionary containing all simulation data

    Raises:
        Exception: If data extraction fails
    """
    try:
        report_data = {}

        # 1. Configuration Results
        report_data["configuration_results"] = _extract_configuration_results(hp_object)

        # 2. Topology & Refrigerant
        report_data["topology_refrigerant"] = _extract_topology_refrigerant(hp_object)

        # 3. State Variables
        report_data["state_variables"] = _extract_state_variables(hp_object)

        # 4. Economic Evaluation
        report_data["economic_evaluation"] = _extract_economic_evaluation(hp_object)

        # 5. Exergy Assessment
        report_data["exergy_assessment"] = _extract_exergy_assessment(hp_object)

        # 6. Full Parameters (for reproducibility)
        report_data["parameters"] = _extract_parameters(hp_object)

        # 7. Model Information
        report_data["model_info"] = _extract_model_info(hp_object)

        logger.info(f"Successfully extracted report data for {hp_object.params.get('setup', {}).get('name', 'unknown')}")

        # Sanitize all data to handle NaN, Infinity, etc.
        report_data = sanitize_for_json(report_data)

        return report_data

    except Exception as e:
        logger.error(f"Failed to extract report data: {e}")
        raise


def _extract_configuration_results(hp_object) -> Dict[str, Any]:
    """Extract configuration results (COP, power, heat output, etc.)."""
    try:
        results = {
            "cop": float(hp_object.cop) if hasattr(hp_object, "cop") and hp_object.cop is not None else None,
        }

        # Extract bus data
        if hasattr(hp_object, "buses") and hp_object.buses:
            if "heat output" in hp_object.buses:
                results["heat_output_w"] = float(hp_object.buses["heat output"].P.val)
            if "power input" in hp_object.buses:
                results["power_input_w"] = float(hp_object.buses["power input"].P.val)
            if "heat input" in hp_object.buses:
                results["heat_input_w"] = float(hp_object.buses["heat input"].P.val)

        # Add convergence status
        results["converged"] = bool(hp_object.solved_design) if hasattr(hp_object, "solved_design") else False

        return results

    except Exception as e:
        logger.warning(f"Error extracting configuration results: {e}")
        return {}


def _extract_topology_refrigerant(hp_object) -> Dict[str, Any]:
    """Extract topology and refrigerant information."""
    try:
        topology_data = {}

        # Topology type
        if hasattr(hp_object, "params") and "setup" in hp_object.params:
            setup = hp_object.params["setup"]
            topology_data["topology_type"] = setup.get("type", "unknown")
            topology_data["model_name"] = setup.get("name", "unknown")

        # Refrigerant information
        if hasattr(hp_object, "wf"):
            topology_data["refrigerant"] = hp_object.wf
        elif hasattr(hp_object, "params") and "setup" in hp_object.params:
            topology_data["refrigerant"] = hp_object.params["setup"].get("refrig", "unknown")

        # For cascade systems
        if hasattr(hp_object, "wf1") and hasattr(hp_object, "wf2"):
            topology_data["refrigerant_low_stage"] = hp_object.wf1
            topology_data["refrigerant_high_stage"] = hp_object.wf2
            topology_data["is_cascade"] = True
        else:
            topology_data["is_cascade"] = False

        return topology_data

    except Exception as e:
        logger.warning(f"Error extracting topology/refrigerant data: {e}")
        return {}


def _extract_state_variables(hp_object) -> Dict[str, Any]:
    """Extract thermodynamic state variables from network results."""
    try:
        state_data = {}

        if hasattr(hp_object, "nw") and hasattr(hp_object.nw, "results"):
            if "Connection" in hp_object.nw.results:
                df = hp_object.nw.results["Connection"]

                # Convert DataFrame to dict (records format for JSON)
                state_data["connections"] = df.to_dict(orient="records")
                state_data["columns"] = list(df.columns)
                state_data["index"] = list(df.index)

                # Extract units if available
                if hasattr(df, "attrs") and "units" in df.attrs:
                    state_data["units"] = df.attrs["units"]
                else:
                    # Default units
                    state_data["units"] = {
                        "m": "kg/s",
                        "p": "bar",
                        "h": "kJ/kg",
                        "T": "°C",
                        "s": "kJ/(kgK)",
                        "v": "m³/kg"
                    }

        return state_data

    except Exception as e:
        logger.warning(f"Error extracting state variables: {e}")
        return {}


def _extract_economic_evaluation(hp_object) -> Dict[str, Any]:
    """Extract economic evaluation data (costs)."""
    try:
        economic_data = {}

        # Total cost
        if hasattr(hp_object, "cost_total"):
            economic_data["total_cost_eur"] = float(hp_object.cost_total)

        # Component costs
        if hasattr(hp_object, "cost") and isinstance(hp_object.cost, dict):
            economic_data["component_costs"] = {
                k: float(v) if isinstance(v, (int, float)) else v
                for k, v in hp_object.cost.items()
            }

        # Specific cost (if heat output available)
        if hasattr(hp_object, "cost_total") and hasattr(hp_object, "buses"):
            if "heat output" in hp_object.buses:
                heat_output_mw = abs(hp_object.buses["heat output"].P.val) / 1e6
                if heat_output_mw > 0:
                    economic_data["specific_cost_eur_per_mw"] = float(
                        hp_object.cost_total / heat_output_mw
                    )

        return economic_data

    except Exception as e:
        logger.warning(f"Error extracting economic evaluation: {e}")
        return {}


def _extract_exergy_assessment(hp_object) -> Dict[str, Any]:
    """Extract exergy analysis data."""
    try:
        exergy_data = {}

        if hasattr(hp_object, "ean") and hp_object.ean is not None:
            # Network-level exergy data
            if hasattr(hp_object.ean, "network_data"):
                network_data = hp_object.ean.network_data
                exergy_data["epsilon"] = float(network_data.get("epsilon", 0))
                exergy_data["E_F_w"] = float(network_data.get("E_F", 0))
                exergy_data["E_P_w"] = float(network_data.get("E_P", 0))
                exergy_data["E_D_w"] = float(network_data.get("E_D", 0))
                exergy_data["E_L_w"] = float(network_data.get("E_L", 0))

            # Component-level exergy data
            if hasattr(hp_object.ean, "component_data"):
                df = hp_object.ean.component_data
                if isinstance(df, pd.DataFrame):
                    exergy_data["component_data"] = df.to_dict(orient="records")
                    exergy_data["component_index"] = list(df.index)

        # Add exergy efficiency from hp object if available
        if hasattr(hp_object, "epsilon"):
            exergy_data["epsilon"] = float(hp_object.epsilon)

        return exergy_data

    except Exception as e:
        logger.warning(f"Error extracting exergy assessment: {e}")
        return {}


def _extract_parameters(hp_object) -> Dict[str, Any]:
    """Extract full parameter set for reproducibility."""
    try:
        if hasattr(hp_object, "params") and isinstance(hp_object.params, dict):
            # Deep copy and convert to JSON-serializable format
            params = _make_json_serializable(hp_object.params)
            return params
        return {}

    except Exception as e:
        logger.warning(f"Error extracting parameters: {e}")
        return {}


def _extract_model_info(hp_object) -> Dict[str, Any]:
    """Extract model metadata."""
    try:
        model_info = {
            "converged": bool(hp_object.solved_design) if hasattr(hp_object, "solved_design") else False,
        }

        # Add topology information
        if hasattr(hp_object, "__class__"):
            model_info["class_name"] = hp_object.__class__.__name__

        # Add component count
        if hasattr(hp_object, "comps") and isinstance(hp_object.comps, dict):
            model_info["component_count"] = len(hp_object.comps)
            model_info["components"] = list(hp_object.comps.keys())

        return model_info

    except Exception as e:
        logger.warning(f"Error extracting model info: {e}")
        return {}


def _make_json_serializable(obj: Any) -> Any:
    """
    Convert object to JSON-serializable format.

    Handles common non-serializable types:
    - DataFrames → dict
    - numpy types → Python natives
    - sets → lists
    - custom objects → dict of attributes
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_make_json_serializable(item) for item in obj)
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Try to convert to dict for custom objects
        try:
            if hasattr(obj, "__dict__"):
                return _make_json_serializable(obj.__dict__)
            return str(obj)
        except:
            return str(obj)


def format_report_summary(report_data: Dict[str, Any]) -> str:
    """
    Format report data into a human-readable summary.

    Args:
        report_data: Report data dictionary

    Returns:
        Formatted string summary
    """
    lines = []
    lines.append("=" * 60)
    lines.append("HEAT PUMP SIMULATION REPORT SUMMARY")
    lines.append("=" * 60)

    # Configuration
    if "configuration_results" in report_data:
        config = report_data["configuration_results"]
        lines.append("\nConfiguration Results:")
        if "cop" in config:
            lines.append(f"  COP: {config['cop']:.3f}")
        if "heat_output_w" in config:
            lines.append(f"  Heat Output: {config['heat_output_w']/1e6:.2f} MW")
        if "power_input_w" in config:
            lines.append(f"  Power Input: {config['power_input_w']/1e6:.2f} MW")

    # Topology
    if "topology_refrigerant" in report_data:
        topo = report_data["topology_refrigerant"]
        lines.append("\nTopology:")
        if "topology_type" in topo:
            lines.append(f"  Type: {topo['topology_type']}")
        if "refrigerant" in topo:
            lines.append(f"  Refrigerant: {topo['refrigerant']}")

    # Economics
    if "economic_evaluation" in report_data:
        econ = report_data["economic_evaluation"]
        lines.append("\nEconomic Evaluation:")
        if "total_cost_eur" in econ:
            lines.append(f"  Total Cost: €{econ['total_cost_eur']:,.2f}")
        if "specific_cost_eur_per_mw" in econ:
            lines.append(f"  Specific Cost: €{econ['specific_cost_eur_per_mw']:,.2f}/MW")

    # Exergy
    if "exergy_assessment" in report_data:
        exergy = report_data["exergy_assessment"]
        lines.append("\nExergy Assessment:")
        if "epsilon" in exergy:
            lines.append(f"  Exergy Efficiency: {exergy['epsilon']*100:.1f}%")

    lines.append("=" * 60)

    return "\n".join(lines)
