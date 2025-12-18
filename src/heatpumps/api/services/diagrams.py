"""
Diagram generation service for heat pump simulation reports.

This module generates matplotlib-based diagrams for thermodynamic cycle visualization:
- P-h (Pressure-Enthalpy) diagrams
- T-s (Temperature-Entropy) diagrams
- Waterfall (Exergy Destruction) diagrams

All diagrams are saved as PNG files to the static/img/diagrams/ directory
and can be served via the /static endpoint.
"""

import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI
from fluprodia import FluidPropertyDiagram

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Service for generating thermodynamic cycle diagrams."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize diagram generator.

        Args:
            output_dir: Directory to save generated diagrams (default: static/img/diagrams/)
        """
        if output_dir is None:
            # Default to static/img/diagrams relative to this file
            output_dir = Path(__file__).parent.parent.parent / "static" / "img" / "diagrams"

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DiagramGenerator initialized with output_dir: {self.output_dir}")

    def generate_ph_diagram(
        self,
        report_id: str,
        refrigerant: str,
        state_points: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Pressure-Enthalpy (P-h) diagram for the thermodynamic cycle.

        Args:
            report_id: Unique report identifier (used for filename)
            refrigerant: Refrigerant name (e.g., 'R134a', 'R1234yf')
            state_points: List of state point dictionaries with keys: p, h, T, s, connection_id
            metadata: Optional metadata for plot title (model_name, topology, etc.)

        Returns:
            Relative path to saved diagram (e.g., 'diagrams/report_id_ph.png')

        Raises:
            ValueError: If state_points is empty or refrigerant is invalid
            RuntimeError: If diagram generation fails
        """
        try:
            if not state_points:
                raise ValueError("state_points cannot be empty")

            logger.info(f"Generating P-h diagram for report {report_id}, refrigerant: {refrigerant}")

            # Extract cycle data
            pressures = []
            enthalpies = []
            labels = []

            for sp in state_points:
                if sp.get('p') is not None and sp.get('h') is not None:
                    # TESPy uses bar and kJ/kg directly, no conversion needed
                    pressures.append(sp['p'])  # Already in bar
                    enthalpies.append(sp['h'])  # Already in kJ/kg
                    # Use index as label if connection_id not available
                    label = sp.get('connection_id', sp.get('id', str(len(labels))))
                    labels.append(label)

            if len(pressures) < 2:
                raise ValueError("Need at least 2 valid state points for P-h diagram")

            # Close the cycle by adding first point at the end
            pressures.append(pressures[0])
            enthalpies.append(enthalpies[0])

            # Try to create fluprodia property plot for refrigerant envelope
            try:
                diagram = FluidPropertyDiagram(refrigerant)
                diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')
                iso_T = np.arange(-50, 200, 25)
                diagram.set_isolines(T=iso_T)
                diagram.calc_isolines()
                diagram.draw_isolines('logph')

                fig = diagram.ax.get_figure()
                ax = diagram.ax

            except Exception as e:
                logger.warning(f"Could not create fluprodia property plot: {e}. Using basic plot.")
                # Fall back to basic plot without refrigerant envelope
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.set_xlabel('Specific Enthalpy h [kJ/kg]', fontsize=12)
                ax.set_ylabel('Pressure p [bar]', fontsize=12)
                ax.set_yscale('log')
                ax.grid(True, alpha=0.3)

            # Plot the cycle
            ax.plot(enthalpies, pressures, 'ro-', linewidth=2.5, markersize=8,
                   label='Heat Pump Cycle', zorder=10)

            # Add state point labels
            for i, label in enumerate(labels):
                if i < len(enthalpies) - 1:  # Don't label the duplicate closing point
                    ax.annotate(label,
                              xy=(enthalpies[i], pressures[i]),
                              xytext=(10, 10),
                              textcoords='offset points',
                              fontsize=10,
                              bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                              zorder=11)

            # Add title
            title = "Pressure-Enthalpy (P-h) Diagram"
            if metadata:
                model_name = metadata.get('model_name', '')
                if model_name:
                    title = f"{title}\n{model_name}"
            ax.set_title(title, fontsize=14, fontweight='bold')

            # Add legend
            ax.legend(loc='best', fontsize=10)

            # Save figure
            filename = f"{report_id}_ph.png"
            filepath = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"P-h diagram saved to {filepath}")
            return f"diagrams/{filename}"

        except Exception as e:
            logger.error(f"Failed to generate P-h diagram: {e}")
            raise RuntimeError(f"P-h diagram generation failed: {str(e)}")

    def generate_ts_diagram(
        self,
        report_id: str,
        refrigerant: str,
        state_points: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Temperature-Entropy (T-s) diagram for the thermodynamic cycle.

        Args:
            report_id: Unique report identifier (used for filename)
            refrigerant: Refrigerant name (e.g., 'R134a', 'R1234yf')
            state_points: List of state point dictionaries with keys: p, h, T, s, connection_id
            metadata: Optional metadata for plot title

        Returns:
            Relative path to saved diagram (e.g., 'diagrams/report_id_ts.png')

        Raises:
            ValueError: If state_points is empty or refrigerant is invalid
            RuntimeError: If diagram generation fails
        """
        try:
            if not state_points:
                raise ValueError("state_points cannot be empty")

            logger.info(f"Generating T-s diagram for report {report_id}, refrigerant: {refrigerant}")

            # Extract cycle data
            temperatures = []
            entropies = []
            labels = []

            for sp in state_points:
                if sp.get('T') is not None and sp.get('s') is not None:
                    # TESPy uses °C and kJ/(kg·K) directly, no conversion needed
                    temperatures.append(sp['T'])  # Already in °C
                    entropies.append(sp['s'])  # Already in kJ/(kg·K)
                    # Use index as label if connection_id not available
                    label = sp.get('connection_id', sp.get('id', str(len(labels))))
                    labels.append(label)

            if len(temperatures) < 2:
                raise ValueError("Need at least 2 valid state points for T-s diagram")

            # Close the cycle
            temperatures.append(temperatures[0])
            entropies.append(entropies[0])

            # Try to create fluprodia property plot
            try:
                diagram = FluidPropertyDiagram(refrigerant)
                diagram.set_unit_system(T='°C', p='bar', s='kJ/kgK')
                iso_p = np.geomspace(0.5, 100, 8)
                diagram.set_isolines(p=iso_p)
                diagram.calc_isolines()
                diagram.draw_isolines('Ts')

                fig = diagram.ax.get_figure()
                ax = diagram.ax

            except Exception as e:
                logger.warning(f"Could not create fluprodia property plot: {e}. Using basic plot.")
                # Fall back to basic plot without refrigerant envelope
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.set_xlabel('Specific Entropy s [kJ/(kg·K)]', fontsize=12)
                ax.set_ylabel('Temperature T [°C]', fontsize=12)
                ax.grid(True, alpha=0.3)

            # Plot the cycle
            ax.plot(entropies, temperatures, 'ro-', linewidth=2.5, markersize=8,
                   label='Heat Pump Cycle', zorder=10)

            # Add state point labels
            for i, label in enumerate(labels):
                if i < len(entropies) - 1:
                    ax.annotate(label,
                              xy=(entropies[i], temperatures[i]),
                              xytext=(10, 10),
                              textcoords='offset points',
                              fontsize=10,
                              bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                              zorder=11)

            # Add title
            title = "Temperature-Entropy (T-s) Diagram"
            if metadata:
                model_name = metadata.get('model_name', '')
                if model_name:
                    title = f"{title}\n{model_name}"
            ax.set_title(title, fontsize=14, fontweight='bold')

            # Add legend
            ax.legend(loc='best', fontsize=10)

            # Save figure
            filename = f"{report_id}_ts.png"
            filepath = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"T-s diagram saved to {filepath}")
            return f"diagrams/{filename}"

        except Exception as e:
            logger.error(f"Failed to generate T-s diagram: {e}")
            raise RuntimeError(f"T-s diagram generation failed: {str(e)}")

    def generate_waterfall_diagram(
        self,
        report_id: str,
        exergy_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Waterfall diagram showing exergy flow from Fuel to Product.

        This matches the Streamlit version which shows:
        - Fuel Exergy at the top
        - Component exergy destruction (sorted by magnitude)
        - Product Exergy at the bottom
        - Exergetic efficiency (epsilon) annotation

        Args:
            report_id: Unique report identifier (used for filename)
            exergy_data: Dictionary with exergy analysis results
            metadata: Optional metadata for plot title

        Returns:
            Relative path to saved diagram (e.g., 'diagrams/report_id_waterfall.png')

        Raises:
            ValueError: If exergy_data is empty or invalid
            RuntimeError: If diagram generation fails
        """
        try:
            if not exergy_data:
                raise ValueError("exergy_data cannot be empty")

            logger.info(f"Generating Waterfall diagram for report {report_id}")
            logger.info(f"Exergy data keys: {list(exergy_data.keys())}")

            # Get network-level data (Fuel Exergy, epsilon)
            E_F = exergy_data.get('E_F_w', 0)  # Fuel exergy in W
            epsilon = exergy_data.get('epsilon', 0)  # Exergetic efficiency

            if E_F <= 0:
                raise ValueError("Fuel exergy (E_F) must be positive")

            # Build component list starting with Fuel Exergy
            comps = ['Fuel Exergy']
            E_D_list = [0]  # Exergy destruction for each row
            E_P_list = [E_F]  # Remaining exergy (product) for each row

            current_E = E_F

            # Extract component-level exergy destruction
            if 'component_data' in exergy_data and 'component_index' in exergy_data:
                component_data = exergy_data['component_data']
                component_index = exergy_data['component_index']

                # Create list of (component_name, E_D) pairs and sort by E_D descending
                comp_ed_pairs = []
                for i, comp_data in enumerate(component_data):
                    if isinstance(comp_data, dict) and 'E_D' in comp_data:
                        e_d = comp_data['E_D']
                        if e_d is not None and isinstance(e_d, (int, float)) and e_d > 1:  # Only > 1 W
                            comp_name = component_index[i] if i < len(component_index) else f"Component {i}"
                            comp_ed_pairs.append((comp_name, e_d))

                # Sort by E_D descending
                comp_ed_pairs.sort(key=lambda x: x[1], reverse=True)

                # Add each component
                for comp_name, e_d in comp_ed_pairs:
                    comps.append(comp_name)
                    E_D_list.append(e_d)
                    current_E = current_E - e_d
                    E_P_list.append(current_E)

            # Add Product Exergy at the end
            comps.append('Product Exergy')
            E_D_list.append(0)
            E_P_list.append(current_E)

            # Convert to kW
            E_D_kW = [e / 1e3 for e in E_D_list]
            E_P_kW = [e / 1e3 for e in E_P_list]

            # Define colors matching Streamlit version
            colors_E_P = ['#74ADC0'] * len(comps)  # Light blue for most
            colors_E_P[0] = '#00395B'  # Dark blue for Fuel Exergy
            colors_E_P[-1] = '#B54036'  # Red for Product Exergy

            # Create figure
            fig, ax = plt.subplots(figsize=(16, 10))

            # Plot horizontal bars (E_P first, then E_D stacked on top)
            y_pos = np.arange(len(comps))
            ax.barh(y_pos, E_P_kW, align='center', color=colors_E_P)
            ax.barh(y_pos, E_D_kW, align='center', left=E_P_kW, label='E_D', color='#EC6707')

            # Add legend
            ax.legend()

            # Add epsilon annotation
            if epsilon > 0:
                ax.annotate(
                    f'$\\epsilon_{{tot}} = ${epsilon:.3f}',
                    (0.96, 0.06),
                    xycoords='axes fraction',
                    ha='right', va='center', color='k',
                    bbox=dict(boxstyle='round,pad=0.3', fc='white')
                )

            # Formatting
            ax.set_xlabel('Exergy in kW')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(comps)
            ax.set_xlim([0, (E_F / 1e3) * 1.1])  # 10% margin
            ax.invert_yaxis()  # Fuel at top, Product at bottom
            ax.grid(axis='x')
            ax.set_axisbelow(True)

            # Save figure
            filename = f"{report_id}_waterfall.png"
            filepath = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Waterfall diagram saved to {filepath}")
            return f"diagrams/{filename}"

        except Exception as e:
            logger.error(f"Failed to generate Waterfall diagram: {e}")
            raise RuntimeError(f"Waterfall diagram generation failed: {str(e)}")

    def generate_all_diagrams(
        self,
        report_id: str,
        refrigerant: str,
        state_points: List[Dict[str, Any]],
        exergy_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate all diagrams for a report (P-h, T-s, and Waterfall).

        Args:
            report_id: Unique report identifier
            refrigerant: Refrigerant name
            state_points: List of thermodynamic state points
            exergy_data: Exergy analysis results
            metadata: Optional metadata

        Returns:
            Dictionary mapping diagram type to relative path:
            {'ph': 'diagrams/id_ph.png', 'ts': 'diagrams/id_ts.png', 'waterfall': 'diagrams/id_waterfall.png'}
        """
        results = {}

        try:
            results['ph'] = self.generate_ph_diagram(report_id, refrigerant, state_points, metadata)
        except Exception as e:
            logger.error(f"Failed to generate P-h diagram: {e}")
            results['ph'] = None

        try:
            results['ts'] = self.generate_ts_diagram(report_id, refrigerant, state_points, metadata)
        except Exception as e:
            logger.error(f"Failed to generate T-s diagram: {e}")
            results['ts'] = None

        try:
            results['waterfall'] = self.generate_waterfall_diagram(report_id, exergy_data, metadata)
        except Exception as e:
            logger.error(f"Failed to generate Waterfall diagram: {e}")
            results['waterfall'] = None

        return results
