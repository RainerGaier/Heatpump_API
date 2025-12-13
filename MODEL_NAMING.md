# Model Naming Convention

## Important: Model Keys vs Class Names

The heatpump simulator uses two different naming conventions that you need to be aware of when using the API:

### Model Keys (lowercase, used by API)

These are the keys used in `hp_models` and `hp_model_classes` dictionaries, and **this is what you should use when calling the API**:

- `simple` - Basic heat pump
- `ihx` - With internal heat exchanger
- `simple_trans` - Transcritical simple cycle
- `econ_closed` - Closed economizer
- `econ_open` - Open economizer
- `cascade` - Cascaded system
- ... and 66 more

**✅ Use these in API requests:**
```json
{
  "model_name": "simple",
  "params": {...}
}
```

### Class Names (PascalCase, internal use)

These are the actual Python class names used internally:

- `HeatPumpSimple`
- `HeatPumpIHX`
- `HeatPumpSimpleTrans`
- `HeatPumpEcon`
- `HeatPumpCascade`
- ... etc

**❌ Do NOT use these in API requests** - they won't work!

## Why Two Naming Conventions?

The codebase has historical reasons for this split:

1. **`parameters.py`** uses class names for loading JSON parameter files
2. **`simulation.py`** uses model keys for instantiating classes
3. **`variables.py`** maintains both mappings

The API automatically handles the conversion between model keys and class names internally.

## Quick Reference

| Model Key | Class Name | Description |
|-----------|------------|-------------|
| simple | HeatPumpSimple | Basic cycle |
| ihx | HeatPumpIHX | With internal IHX |
| simple_trans | HeatPumpSimpleTrans | Transcritical basic |
| ic | HeatPumpIC | With intercooling |
| econ_closed | HeatPumpEcon | Closed economizer |
| econ_open | HeatPumpEcon | Open economizer |
| flash | HeatPumpFlash | Flash tank |
| cascade | HeatPumpCascade | Cascaded system |

## How to Find Available Models

Use the API to list all available models with their keys:

```bash
curl http://localhost:8000/api/v1/models
```

This returns:
```json
{
  "models": [
    {
      "name": "simple",
      "display_name": "Basic",
      "topology": "Simple",
      ...
    },
    ...
  ]
}
```

The `"name"` field is what you should use in simulation requests.
