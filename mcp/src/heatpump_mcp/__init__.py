"""
Heat Pump MCP Server Package

This package provides an MCP (Model Context Protocol) server that enables
Claude Desktop to run heat pump simulations via the deployed Cloud Run API.

Usage:
    # As a command-line tool (after pip install):
    heatpump-mcp

    # Or run directly:
    python -m heatpump_mcp
"""

__version__ = "1.0.0"
__author__ = "Rainer Gaier"

from .server import main, app

__all__ = ["main", "app", "__version__"]
