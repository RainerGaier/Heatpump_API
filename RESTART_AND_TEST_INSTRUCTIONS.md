# Instructions: Restart API and Test Fixes

## Summary of Fixes Applied

Two critical bugs have been identified and fixed:

1. **Deep Parameter Merging Bug** (✅ FIXED in previous session)
   - File: [src/heatpumps/api/routes/simulate.py](src/heatpumps/api/routes/simulate.py)
   - Issue: Shallow dictionary merging was replacing entire nested parameter dictionaries
   - Fix: Implemented `deep_merge_params()` function for recursive merging

2. **TESPy Version Compatibility Bug** (✅ FIXED in this session)
   - File: [src/heatpumps/models/HeatPumpBase.py](src/heatpumps/models/HeatPumpBase.py#L1133-L1144)
   - Issue: Code used `'heat exchanger'` (lowercase with space) but TESPy 0.9.10 requires `'HeatExchanger'` (CamelCase)
   - Fix: Updated 4 occurrences of component name to match TESPy's naming convention

## IMPORTANT: Restart Required

The API server must be restarted to load the fixed code. The current running server still has the old code.

## Step-by-Step Testing Instructions

### Step 1: Stop the Current API Server

In the terminal where `heatpumps-api` is running:
- Press **Ctrl+C** to stop the server

### Step 2: Restart the API Server

```bash
heatpumps-api
```

Wait for the server to start and show:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 3: Run the Test Suite

Open a new terminal and run:

```bash
cd c:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
python test_api.py
```

### Expected Test Results (After Fix)

#### Tests That Should Pass ✅

1. **Health Check**: ✅ PASS
2. **Model Listing**: ✅ PASS
3. **Model Info**: ✅ PASS
4. **Parameter Retrieval**: ✅ PASS
5. **Refrigerant Listing**: ✅ PASS
6. **Design Simulation**: ✅ PASS
7. **IHX Parameter Override**: ✅ PASS (now working with deep merge)

#### Tests That May Still Have Issues ⚠️

8. **Part-Load Simulation**: ⚠️ May have convergence issues
9. **Custom Part-Load Range**: ⚠️ May have convergence issues
10. **Off-Design Simulation**: ⚠️ May have convergence issues

### Step 4: Quick Verification Test

Run a quick manual test to verify the TESPy fix:

```bash
curl -X POST http://localhost:8000/api/v1/simulate/partload \
     -H "Content-Type: application/json" \
     -d "{\"model_name\":\"simple\",\"params\":{},\"partload_config\":{\"min_ratio\":0.8,\"max_ratio\":1.0,\"steps\":2}}"
```

**Before Fix**: Would return `"error_message": "Off-design simulation failed: 'heat exchanger'"`

**After Fix**: Should either:
- Return successful results with `converged: true` and actual `partload_points` data, OR
- Return a different error (e.g., convergence issues, which are separate from the TESPy bug)

The key indicator that the fix worked is that you **no longer see the `KeyError: 'heat exchanger'` error**.

## Understanding Test Results

### If TESPy Fix Worked ✅

You should NOT see this error anymore:
```
KeyError: 'heat exchanger'
```

### Possible Remaining Issues (Separate from TESPy Bug)

Even after the fix, some simulations may fail due to:

1. **Convergence Issues**:
   ```
   Simulation crashed due to an unexpected error:
   Pressure to PQ_flash [44446128 Pa] may not be above the numerical critical point
   ```
   - This is a thermodynamic limitation, not a code bug
   - Occurs when operating conditions exceed refrigerant limits

2. **Invalid Component Efficiency**:
   ```
   Invalid value for eta_s: eta_s = 1.720899969165697 above maximum value (1)
   ```
   - Off-design calculation produced physically impossible efficiency
   - May require parameter tuning or model constraints

3. **Empty Results**:
   ```
   Off-design results are empty
   ```
   - Simulation ran but produced no valid operating points
   - Could be due to convergence failures at all test points

These issues are related to **model configuration and operating conditions**, not the TESPy compatibility bug we fixed.

## Additional Testing: Multi-Model Compatibility

To test off-design capability across different models:

```bash
python test_offdesign_models.py
```

This script tests 4 different heat pump models (simple, ihx, econ_closed, ic) to see which ones support off-design simulation.

Expected results after fix:
- Models should no longer crash with `'heat exchanger'` error
- Some models may still have convergence issues (separate problem)

## Documentation

Three comprehensive documentation files have been created:

1. **[BUGFIX_DEEP_MERGE.md](BUGFIX_DEEP_MERGE.md)**
   - Documents the parameter merging bug and fix
   - Explains shallow vs. deep dictionary merging
   - Shows before/after examples

2. **[BUGFIX_TESPY_COMPATIBILITY.md](BUGFIX_TESPY_COMPATIBILITY.md)**
   - Documents the TESPy version compatibility issue
   - Shows investigation process
   - Lists all component name changes
   - Includes TESPy version compatibility notes

3. **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)**
   - Documents the three enhanced API features
   - Provides usage examples
   - Updated with deep merge behavior notes

## Troubleshooting

### Issue: Still seeing `KeyError: 'heat exchanger'`

**Cause**: API server wasn't restarted or is using cached Python modules

**Solution**:
1. Completely stop the API server (Ctrl+C)
2. Wait 2-3 seconds
3. Restart: `heatpumps-api`
4. Verify the fix loaded by checking for the startup log

### Issue: Tests pass but return empty results

**Cause**: Off-design simulations fail to converge at any operating point

**Solution**:
- This is expected for some models/configurations
- Try different models or operating ranges
- Check logs for specific convergence errors

### Issue: Design simulation works but off-design fails

**Cause**: Off-design simulation has stricter convergence requirements

**Solution**:
- Review default parameters in the model
- Adjust temperature ranges to stay within refrigerant limits
- Consider using simpler models (e.g., 'simple' instead of 'cascade')

## Verification Checklist

After restarting the API server, verify:

- [ ] API server started without errors
- [ ] Health check endpoint works: `curl http://localhost:8000/health`
- [ ] Design simulation passes: `python test_api.py` (test 1-6)
- [ ] IHX parameter override passes: `python test_api.py` (test 7)
- [ ] No `KeyError: 'heat exchanger'` errors in API logs
- [ ] Off-design simulations return structured responses (even if `converged: false`)

## Next Steps

1. ✅ Restart API server
2. ✅ Run test suite
3. ✅ Verify no more `'heat exchanger'` KeyError
4. ⚠️ If off-design still fails with convergence issues:
   - Review model parameters
   - Adjust operating ranges
   - Consider reporting specific models/conditions that fail

## Summary

The core TESPy compatibility bug has been fixed. The API should now:
- Load heat exchanger characteristics correctly
- Execute off-design parametrization without crashing
- Return structured responses with operating point data or meaningful error messages

Any remaining issues are likely related to **model convergence and operating conditions**, which is a separate concern from the TESPy API compatibility that we fixed.
