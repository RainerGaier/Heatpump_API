# Fresh Install Guide

This guide will help you create a fresh installation of the Heatpump API from your GitHub repository.

## Prerequisites

- Git installed
- Python 3.11 or higher
- Internet connection

## Step-by-Step Fresh Install

### 1. Create a New Directory

Choose where you want to install the project:

```bash
# Example location (adjust as needed)
cd C:\Users\gaierr\Energy_Projects\projects
mkdir heatpump-fresh-install
cd heatpump-fresh-install
```

### 2. Clone the Repository

```bash
git clone https://github.com/RainerGaier/Heatpump_API.git
cd Heatpump_API
```

### 3. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
# source venv/bin/activate
```

### 4. Install the Package

```bash
# Install in editable mode with all dependencies
pip install -e .
```

This will:
- ✅ Install all required dependencies (CoolProp, TESPy, Streamlit, etc.)
- ✅ Install the package in editable mode
- ✅ Create the `heatpumps-dashboard` command

### 5. Verify Installation

```bash
# Check package is installed
pip show heatpumps

# Should show:
# Name: heatpumps
# Version: 0.1.0
# Location: ...
```

### 6. Run the Dashboard

```bash
heatpumps-dashboard
```

The dashboard will open at: http://localhost:8501

### 7. (Optional) Install Development Dependencies

If you plan to contribute or develop:

```bash
pip install -e ".[dev]"
```

This installs additional tools:
- pytest (testing)
- black (code formatting)
- ruff (linting)
- mypy (type checking)

## Quick Start Commands

```bash
# All in one:
cd C:\Users\gaierr\Energy_Projects\projects
mkdir heatpump-fresh-install && cd heatpump-fresh-install
git clone https://github.com/RainerGaier/Heatpump_API.git
cd Heatpump_API
python -m venv venv
venv\Scripts\activate
pip install -e .
heatpumps-dashboard
```

## Data Storage

Simulation data will be stored in:
```
C:\Users\<your-username>\.heatpumps\
├── stable\     # Simulation designs
└── output\     # Results and plots
```

## Troubleshooting

### Problem: Command not found

**Solution:** Make sure you activated the virtual environment:
```bash
venv\Scripts\activate
```

### Problem: Permission errors

**Solution:** This shouldn't happen with the new version, but if it does:
- Make sure you have write permissions to `C:\Users\<username>\.heatpumps\`
- Try running without administrator privileges

### Problem: Missing dependencies

**Solution:** Reinstall with dependencies:
```bash
pip install --force-reinstall -e .
```

### Problem: Import errors

**Solution:** Make sure you're in the virtual environment and the package is installed:
```bash
# Activate venv
venv\Scripts\activate

# Reinstall
pip install -e .
```

## Uninstalling

To remove the package:

```bash
# Uninstall package
pip uninstall heatpumps

# Optionally, remove user data
# rm -rf C:\Users\<username>\.heatpumps

# Optionally, remove virtual environment
# deactivate
# cd ..
# rmdir /s venv
```

## Testing the Fresh Install

After installation, test that everything works:

```bash
# Test imports
python -c "from heatpumps.models import HeatPumpSimple; print('✓ Imports work')"

# Test package info
python -c "from heatpumps import __version__; print(f'Version: {__version__}')"

# Run dashboard
heatpumps-dashboard
```

## What's Included

This fresh install includes all the fixes:
- ✅ Proper package configuration
- ✅ Permission error fixes
- ✅ Import path fixes
- ✅ Theme/image display fixes
- ✅ Console command registration
- ✅ Comprehensive documentation

## Next Steps

1. Explore the dashboard
2. Try different heat pump configurations
3. Review the documentation in `/docs`
4. Check out example usage in the README

## Support

If you encounter issues:
1. Check `FIXES_COMPLETE.md` for known issues
2. Review `INSTALL.md` for detailed installation options
3. Create an issue on GitHub

---

Happy simulating! 🚀
