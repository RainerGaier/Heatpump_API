# Permission Error Fix

## Problem
When running `heatpumps-dashboard`, you encountered:
```
PermissionError: [Errno 13] Permission denied:
'C:\\Users\\gaierr\\Energy_Projects\\projects\\heatpumps\\heatpumps-main\\src\\heatpumps\\models\\stable\\HeatPumpSimple_R717_design'
```

## Root Cause
The application was trying to save simulation results to the package's own directory structure (`src/heatpumps/models/stable/`), which can cause permission issues depending on:
- How the package is installed (editable vs regular)
- Operating system permissions
- Whether the directory is in a protected location

## Solution Implemented

Modified `HeatPumpBase.py` to use a **user data directory** for write operations:

### Changes Made

1. **New Path Strategy:**
   - Simulation data: `~/.heatpumps/stable/`
   - Output files: `~/.heatpumps/output/`
   - Falls back to package directory if writable (for development)

2. **Smart Directory Detection:**
   - First tries to use package directory (for editable installs)
   - Automatically falls back to user directory if permission denied
   - Creates directories as needed with proper permissions

3. **Updated Methods:**
   - `_init_dir_paths()` - Now uses user data directory
   - `validate_dir()` - Creates directories with `makedirs(exist_ok=True)`
   - All output paths updated to use `self.output_base`
   - All stable paths updated to use `self.stable_base`

### User Data Directory Locations

**Windows:**
```
C:\Users\<username>\.heatpumps\
├── stable\         # Simulation designs and states
└── output\         # Generated plots and results
    └── logging\    # Simulation logs
```

**Linux/Mac:**
```
/home/<username>/.heatpumps/
├── stable/
└── output/
    └── logging/
```

## Benefits

✅ **No Permission Errors** - User directory is always writable
✅ **Clean Separation** - User data separate from package code
✅ **Portable** - Works with any installation method
✅ **Standard Practice** - Follows OS conventions for application data
✅ **Backward Compatible** - Still works with existing code

## Testing

Test that the fix works:

```python
from heatpumps.models import HeatPumpSimple
from heatpumps.parameters import get_params

params = get_params('HeatPumpSimple')
hp = HeatPumpSimple(params=params)

print(f"Stable dir: {hp.stable_base}")
print(f"Output dir: {hp.output_base}")
# Should show paths in your home directory
```

## Now You Can Run

```bash
heatpumps-dashboard
```

The dashboard should start without permission errors!

## Note on Existing Data

If you have existing simulation data in the package directory, it will still be read from there. New simulations will be saved to the user data directory.

To clean up old data:
```bash
# View your new data directory
ls ~/.heatpumps

# Old package data (can be deleted after migration)
# C:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main\src\heatpumps\models\stable
```
