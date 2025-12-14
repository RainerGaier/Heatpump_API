# Model Change - Clear Old Results Fix

**Date:** 2025-12-14
**Issue:** Old simulation results remain visible when changing model type
**Status:** ✅ **FIXED**

---

## Problem Description

When a user runs a simulation, then changes the heat pump model type, the old simulation results remain displayed on the screen even though they're no longer valid for the new model.

**User Experience:**
1. Select "Simple" model → Run simulation → See results
2. Change to "Cascade" model → Topology diagram updates
3. **Problem:** Old "Simple" results still shown (COP, state variables, etc.)
4. User must manually reload page or results are confusing

This creates confusion because:
- Results don't match the selected model
- COP and metrics are for the wrong topology
- State variables are for different refrigerants
- User might think the new model has same performance

---

## Root Cause

When model selection changes, Streamlit correctly updates the topology diagram and input parameters, but the simulation results (`ss.hp`) persist in session state because nothing clears them.

The results only get replaced when:
- User clicks "Run Configuration" again
- User manually reloads the page

This is another session state management issue - we need to detect when the model changes and proactively clear stale data.

---

## The Fix

**File:** `src/heatpumps/hp_dashboard.py` (lines 295-303)

Added a check after model selection that compares the current model to the previous model and clears results if they differ:

```python
# Clear old simulation results if model type changed
if 'previous_model' in ss and ss.previous_model != hp_model_name:
    # Model changed - clear old results
    if 'hp' in ss:
        del ss.hp
    if 'partload_char' in ss:
        del ss.partload_char
# Store current model for next comparison
ss.previous_model = hp_model_name
```

### How It Works

1. **First time:** No `previous_model` in session state → Just store current model
2. **Subsequent runs:** Check if `previous_model` matches `hp_model_name`
   - **Match:** No change, keep results
   - **Different:** Model changed! Clear `ss.hp` and `ss.partload_char`
3. **Always:** Update `previous_model` to current selection

---

## What Gets Cleared

When the model changes, we clear:

### `ss.hp` - Main simulation results
Contains:
- COP, power, heat output
- State variables (all connection points)
- Economic evaluation
- Exergy assessment
- TESPy network object

### `ss.partload_char` - Part-load simulation data
Contains:
- Operating characteristics over load range
- COP curves
- Efficiency maps

### What Stays
- User input parameters (temperatures, pressures, etc.)
- UI selections (model type, refrigerant, etc.)
- Configuration mode

---

## User Experience

### Before Fix
```
User: Select "Simple" model
User: Run simulation
UI: Shows Simple results (COP: 4.2)

User: Change to "Cascade" model
UI: Topology diagram updates to Cascade
UI: Still shows "COP: 4.2" ← Wrong! This is from Simple model

User: Confused - thinks Cascade has COP 4.2
```

### After Fix
```
User: Select "Simple" model
User: Run simulation
UI: Shows Simple results (COP: 4.2)

User: Change to "Cascade" model
UI: Topology diagram updates to Cascade
UI: Results disappear ← Correct! Old data cleared
UI: Shows only input parameters

User: Clicks "Run Configuration"
UI: Shows new Cascade results (COP: 3.8) ← Correct!
```

---

## Technical Details

### State Tracking Pattern

This uses a common Streamlit pattern for detecting changes:

```python
# Pattern: Detect when value changes
if 'previous_value' in st.session_state:
    if st.session_state.previous_value != current_value:
        # Value changed! Do something
        handle_change()

# Always update stored value
st.session_state.previous_value = current_value
```

### Why `del` Instead of Setting to None

We use `del ss.hp` instead of `ss.hp = None` because:

1. **Consistency:** The `if 'hp' in ss:` checks throughout the code expect the key to not exist when there's no simulation
2. **Memory:** Completely removes the object, freeing memory
3. **Clarity:** Missing key clearly means "no simulation yet"

If we set to `None`, we'd need to change all checks from:
```python
if 'hp' in ss:  # Clean
```
to:
```python
if 'hp' in ss and ss.hp is not None:  # Verbose
```

---

## Edge Cases Handled

### Case 1: First Load
- No `previous_model` in session state
- Check `'previous_model' in ss` returns False
- Skip the clearing logic
- Just store the model

### Case 2: Same Model Selected Again
- `previous_model` matches `hp_model_name`
- Don't clear results
- Results persist (desired behavior)

### Case 3: Model Changes Multiple Times
- Each change clears the previous model's results
- Always starts fresh with new model

### Case 4: Switching Modes
- Switching from Configuration to Partial Load
- Results stay (desired - same model)
- Only clears when model type actually changes

---

## What Triggers Clearing

Results are cleared when:
- ✅ Changing from "Simple" to "IHX"
- ✅ Changing from "IHX" to "Cascade"
- ✅ Changing from subcritical to transcritical process
- ✅ Changing from "Simple" to "Simple | Transcritical"

Results are NOT cleared when:
- ✅ Adjusting temperature sliders (same model)
- ✅ Changing refrigerant (same model)
- ✅ Switching to Partial Load mode (same model)
- ✅ Using any other controls

---

## Similar Pattern Used Elsewhere

This same pattern is used for:
- Mode switching (Configuration vs Partial Load)
- Parameter validation
- Form state management

Example from line 256:
```python
ss.rerun_req = True
```

This sets a flag to track state changes, similar to our `previous_model` tracking.

---

## Testing

### Test Case 1: Simple → IHX
1. Select "Simple" model
2. Run simulation → See results
3. Change to "IHX" model
4. **Expected:** Results disappear, only topology shown
5. Run new simulation → See new results

### Test Case 2: Back and Forth
1. Select "Simple" → Run → See results
2. Change to "IHX" → Results clear
3. Change back to "Simple" → Results still cleared
4. Run again → See new results

### Test Case 3: Cascade (After Bug Fix)
1. Select "Cascade" model
2. Run simulation → See results
3. Click "Save & Share Report" → Works!
4. Change to "Simple" → Results clear
5. Old cascade data gone

---

## Why This Matters for Phase 1

The "Save & Share Report" button relies on `ss.hp` containing valid data. Before this fix:

1. User runs "Simple" simulation
2. User changes to "Cascade" model (old results stay)
3. User clicks "Save & Share Report"
4. **Bug:** Report contains "Simple" data but user thinks it's "Cascade"!

After fix:
1. User runs "Simple" simulation
2. User changes to "Cascade" model (old results cleared)
3. **No button** - results section hidden (no `ss.hp`)
4. User must run new simulation first
5. User clicks "Save & Share Report"
6. **Correct:** Report contains valid "Cascade" data

---

## Code Location

**File:** `src/heatpumps/hp_dashboard.py`
**Lines:** 295-303
**Location in flow:** After model selection, before parameter loading

```python
Line 260-293: Model selection logic (selectboxes, radio buttons)
Line 295-303: ← NEW: Clear old results if model changed
Line 305-309: Load parameters for selected model
```

---

## Performance Impact

**Negligible:**
- One dictionary lookup: `'previous_model' in ss` (O(1))
- One string comparison: `ss.previous_model != hp_model_name` (O(1))
- Two deletions if needed: `del ss.hp` (O(1))
- Happens once per page load, not per interaction

---

## Alternative Approaches Considered

### Option 1: Clear on every rerun
```python
# Always clear results on Configuration page
if mode == 'Configuration' and 'hp' in ss:
    del ss.hp
```
**Rejected:** Too aggressive - clears results even when just adjusting parameters

### Option 2: Require explicit "Clear" button
```python
if st.button("Clear Results"):
    del ss.hp
```
**Rejected:** Extra click required, poor UX

### Option 3: Warning message instead of clearing
```python
if model_changed:
    st.warning("Results are from previous model")
```
**Rejected:** Still confusing, doesn't solve the problem

### Option 4: Show both old and new results
**Rejected:** Cluttered, takes up too much screen space

**Chosen approach:** Automatic clearing is cleanest and least surprising.

---

## Summary

✅ **Problem:** Old results shown when model changes
✅ **Solution:** Detect model changes and clear stale results
✅ **Impact:** Cleaner UX, prevents confusion
✅ **Risk:** None - only clears when model actually changes
✅ **Lines added:** 8
✅ **Backwards compatible:** Yes

---

**Status:** ✅ Fixed and ready for testing
**Testing:** Change model types in Streamlit and verify results clear
**Commit with:** Cascade fix and Phase 1 (or separate commit)
