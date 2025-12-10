"""
heatpumps - Steady-state simulation of heat pump topologies

This package provides tools for simulating various heat pump configurations
using TESPy (Thermal Engineering Systems in Python).
"""

__version__ = "0.1.0"
__author__ = "Jonas Freissmann and Malte Fritz"

# Make key classes easily importable
from heatpumps.parameters import get_params

__all__ = ['get_params', '__version__']
