# Installation Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for development installation)

## Installation Methods

### Method 1: Development Installation (Recommended for Contributors)

For an editable installation that allows you to modify the code:

```bash
# Clone the repository (if not already done)
git clone https://github.com/jfreissmann/heatpumps.git
cd heatpumps

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Method 2: Standard Installation

For a standard installation from the local directory:

```bash
cd heatpumps
pip install .
```

### Method 3: Build and Install Distribution

To build distribution packages:

```bash
# Install build tools
pip install build

# Build the package
python -m build

# This creates:
# - dist/heatpumps-0.1.0.tar.gz (source distribution)
# - dist/heatpumps-0.1.0-py3-none-any.whl (wheel distribution)

# Install from the wheel
pip install dist/heatpumps-0.1.0-py3-none-any.whl
```

## Verify Installation

After installation, verify that the package is correctly installed:

```bash
# Check if the package is installed
pip show heatpumps

# Test the dashboard command
heatpumps-dashboard
```

## Running the Dashboard

Once installed, you can launch the dashboard with:

```bash
heatpumps-dashboard
```

This will open the Streamlit dashboard in your default web browser.

## Using the Package in Python Scripts

```python
from heatpumps.models import HeatPumpSimple
from heatpumps.parameters import get_params

# Get default parameters for a simple heat pump
params = get_params('HeatPumpSimple')

# Customize parameters
params['setup']['refrig'] = 'R1234yf'
params['fluids']['wf'] = 'R1234yf'
params['C3']['T'] = 85  # feed flow temperature
params['C1']['T'] = 50  # return flow temperature

# Create and run the model
hp = HeatPumpSimple(params=params)
hp.run_model()

# Generate state diagram
hp.generate_state_diagram(diagram_type='logph', savefig=True)
```

## Development Setup

If you're contributing to the project:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=heatpumps --cov-report=html

# Format code with black
black src/heatpumps

# Lint with ruff
ruff check src/heatpumps
```

## Troubleshooting

### Installation Issues

If you encounter issues with oemof.thermal installation (Git dependency):

```bash
# Install Git if not already installed
# Then try installing again
pip install --upgrade pip
pip install -e .
```

### Platform-Specific Notes

**Windows:**
- Use `venv\Scripts\activate` to activate virtual environment
- Ensure Git is installed for GitHub dependencies

**macOS/Linux:**
- Use `source venv/bin/activate` to activate virtual environment
- May need to install system dependencies for matplotlib/numpy

## Uninstallation

To uninstall the package:

```bash
pip uninstall heatpumps
```
