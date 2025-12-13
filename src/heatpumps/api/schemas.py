"""
Pydantic schemas for request/response validation.

These models define the structure of API requests and responses,
providing automatic validation and documentation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# Configuration Schemas for Off-Design and Part-Load
class PartloadConfig(BaseModel):
    """Configuration for part-load simulation range."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "min_ratio": 0.3,
            "max_ratio": 1.0,
            "steps": 8
        }
    })

    min_ratio: float = Field(
        0.3,
        ge=0.0,
        le=1.5,
        description="Minimum load ratio (0.0-1.5, typically 0.3)",
    )
    max_ratio: float = Field(
        1.0,
        ge=0.0,
        le=1.5,
        description="Maximum load ratio (0.0-1.5, typically 1.0)",
    )
    steps: Optional[int] = Field(
        None,
        ge=2,
        le=50,
        description="Number of load points (auto-calculated if None)",
    )

    @field_validator('max_ratio')
    @classmethod
    def validate_max_greater_than_min(cls, v, info):
        if 'min_ratio' in info.data and v <= info.data['min_ratio']:
            raise ValueError('max_ratio must be greater than min_ratio')
        return v


class TemperatureRange(BaseModel):
    """Configuration for temperature sweep range."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "constant": False,
            "start": 5.0,
            "end": 20.0,
            "steps": 6
        }
    })

    constant: bool = Field(
        True,
        description="Keep temperature constant (use design point value)",
    )
    start: Optional[float] = Field(
        None,
        ge=-50.0,
        le=200.0,
        description="Starting temperature in °C (required if not constant)",
    )
    end: Optional[float] = Field(
        None,
        ge=-50.0,
        le=200.0,
        description="Ending temperature in °C (required if not constant)",
    )
    steps: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Number of temperature points (auto-calculated if None)",
    )

    @model_validator(mode='after')
    def validate_range(self):
        if not self.constant:
            if self.start is None or self.end is None:
                raise ValueError('start and end temperatures required when constant=False')
            if self.end <= self.start:
                raise ValueError('end temperature must be greater than start temperature')
        return self


class OffdesignConfig(BaseModel):
    """Configuration for off-design simulation."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "heat_source_range": {
                "constant": False,
                "start": 5.0,
                "end": 20.0,
                "steps": 6
            },
            "heat_sink_range": {
                "constant": False,
                "start": 30.0,
                "end": 55.0,
                "steps": 6
            },
            "partload_range": {
                "min_ratio": 0.3,
                "max_ratio": 1.0,
                "steps": 8
            }
        }
    })

    heat_source_range: Optional[TemperatureRange] = Field(
        None,
        description="Heat source temperature sweep configuration",
    )
    heat_sink_range: Optional[TemperatureRange] = Field(
        None,
        description="Heat sink temperature sweep configuration",
    )
    partload_range: Optional[PartloadConfig] = Field(
        None,
        description="Part-load ratio sweep configuration",
    )


# Request Schemas
class SimulationRequest(BaseModel):
    """Request schema for running a heat pump simulation."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "model_name": "simple",
            "econ_type": None,
            "params": {
                "T_hs_ff": 10.0,
                "T_cons_ff": 35.0,
            },
            "run_offdesign": False,
            "run_partload": False,
        }
    })

    model_name: str = Field(
        ...,
        description="Name of the heat pump model to simulate (use lowercase model key)",
        examples=["simple", "ihx", "econ_closed"],
    )
    econ_type: Optional[str] = Field(
        None,
        description="Economizer type for models that support it (closed, open, closed_ihx, open_ihx)",
        examples=["closed", "open"],
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Simulation parameters to override defaults",
    )
    run_offdesign: bool = Field(
        False,
        description="Whether to run off-design simulation",
    )
    run_partload: bool = Field(
        False,
        description="Whether to run part-load characteristics simulation",
    )
    partload_config: Optional[PartloadConfig] = Field(
        None,
        description="Part-load range configuration (if None, uses defaults)",
    )
    offdesign_config: Optional[OffdesignConfig] = Field(
        None,
        description="Off-design simulation configuration (if None, uses defaults)",
    )


class AsyncSimulationRequest(SimulationRequest):
    """Request schema for asynchronous simulation with callback support."""

    webhook_url: Optional[str] = Field(
        None,
        description="Optional webhook URL to POST results when simulation completes",
    )


# Response Schemas
class SimulationResult(BaseModel):
    """Response schema for simulation results."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "model_name": "HeatPumpSimple",
            "converged": True,
            "cop": 4.23,
            "epsilon": 0.58,
            "heat_output": 10500.0,
            "power_input": 2482.0,
            "cost_total": 125000.0,
        }
    })

    model_name: str
    converged: bool
    cop: Optional[float] = Field(None, description="Coefficient of Performance")
    epsilon: Optional[float] = Field(None, description="Exergy efficiency")
    heat_output: Optional[float] = Field(None, description="Heat output in W")
    power_input: Optional[float] = Field(None, description="Power input in W")
    cost_total: Optional[float] = Field(None, description="Total cost estimate")
    error_message: Optional[str] = Field(None, description="Error message if simulation failed")


class StatePoint(BaseModel):
    """Single state point in the thermodynamic cycle."""

    connection_id: str
    T: Optional[float] = Field(None, description="Temperature in K")
    p: Optional[float] = Field(None, description="Pressure in Pa")
    h: Optional[float] = Field(None, description="Specific enthalpy in J/kg")
    s: Optional[float] = Field(None, description="Specific entropy in J/(kg*K)")
    m: Optional[float] = Field(None, description="Mass flow rate in kg/s")
    fluid: Optional[str] = Field(None, description="Fluid composition")


class DetailedSimulationResult(SimulationResult):
    """Extended simulation results with state points and exergy data."""

    state_points: Optional[List[StatePoint]] = Field(None, description="Thermodynamic state points")
    exergy_analysis: Optional[Dict[str, Any]] = Field(None, description="Exergy analysis results")
    component_data: Optional[Dict[str, Any]] = Field(None, description="Component-specific data")


class OffdesignPoint(BaseModel):
    """Single operating point in off-design simulation."""

    T_hs_ff: float = Field(..., description="Heat source flow temperature (°C)")
    T_cons_ff: float = Field(..., description="Heat sink flow temperature (°C)")
    partload_ratio: float = Field(..., description="Part-load ratio")
    cop: Optional[float] = Field(None, description="Coefficient of Performance")
    heat_output: Optional[float] = Field(None, description="Heat output in W")
    power_input: Optional[float] = Field(None, description="Power input in W")
    epsilon: Optional[float] = Field(None, description="Exergy efficiency")
    converged: bool = Field(True, description="Whether this point converged")


class OffdesignResult(BaseModel):
    """Results from off-design simulation sweep."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "model_name": "simple",
            "converged": True,
            "design_cop": 4.23,
            "design_heat_output": 10500000.0,
            "temperature_range": {
                "T_hs_ff": [5.0, 10.0, 15.0, 20.0],
                "T_cons_ff": [30.0, 40.0, 50.0]
            },
            "partload_range": [0.3, 0.5, 0.75, 1.0],
            "operating_points": [
                {
                    "T_hs_ff": 10.0,
                    "T_cons_ff": 40.0,
                    "partload_ratio": 1.0,
                    "cop": 4.23,
                    "heat_output": 10500000.0,
                    "power_input": 2482000.0,
                    "converged": True
                }
            ],
            "total_points": 48,
            "converged_points": 46
        }
    })

    model_name: str
    converged: bool
    design_cop: Optional[float] = Field(None, description="COP at design point")
    design_heat_output: Optional[float] = Field(None, description="Heat output at design point in W")
    temperature_range: Optional[Dict[str, List[float]]] = Field(
        None,
        description="Temperature ranges simulated (T_hs_ff and T_cons_ff arrays)",
    )
    partload_range: Optional[List[float]] = Field(
        None,
        description="Part-load ratios simulated",
    )
    operating_points: List[OffdesignPoint] = Field(
        default_factory=list,
        description="All simulated operating points",
    )
    total_points: int = Field(..., description="Total number of simulated points")
    converged_points: int = Field(..., description="Number of converged points")
    error_message: Optional[str] = Field(None, description="Error message if simulation failed")


class PartloadPoint(BaseModel):
    """Single part-load operating point."""

    load_ratio: float = Field(..., description="Part-load ratio (0.0-1.0)")
    cop: Optional[float] = Field(None, description="Coefficient of Performance at this load")
    heat_output: Optional[float] = Field(None, description="Heat output in W")
    power_input: Optional[float] = Field(None, description="Power input in W")
    epsilon: Optional[float] = Field(None, description="Exergy efficiency")
    converged: bool = Field(True, description="Whether this point converged")


class PartloadResult(BaseModel):
    """Results from part-load characteristics simulation."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "model_name": "simple",
            "converged": True,
            "design_cop": 4.23,
            "partload_points": [
                {"load_ratio": 0.3, "cop": 3.85, "heat_output": 3150.0, "power_input": 818.2, "converged": True},
                {"load_ratio": 0.5, "cop": 4.12, "heat_output": 5250.0, "power_input": 1274.5, "converged": True},
                {"load_ratio": 1.0, "cop": 4.23, "heat_output": 10500.0, "power_input": 2482.0, "converged": True}
            ],
            "total_points": 8,
            "converged_points": 8
        }
    })

    model_name: str
    converged: bool
    design_cop: Optional[float] = Field(None, description="COP at design point")
    design_heat_output: Optional[float] = Field(None, description="Heat output at design point in W")
    partload_points: List[PartloadPoint] = Field(default_factory=list, description="Part-load operating points")
    total_points: int = Field(..., description="Total number of simulated points")
    converged_points: int = Field(..., description="Number of converged points")
    error_message: Optional[str] = Field(None, description="Error message if simulation failed")


# Task/Job Schemas
class TaskStatus(BaseModel):
    """Status of an asynchronous task."""

    task_id: str
    status: str = Field(..., description="Task status: pending, running, completed, failed")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[SimulationResult] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str
    updated_at: str


class TaskResponse(BaseModel):
    """Response when submitting an asynchronous task."""

    task_id: str
    status: str
    message: str
    status_url: str = Field(..., description="URL to check task status")


# Model Information Schemas
class ModelInfo(BaseModel):
    """Information about a heat pump model."""

    name: str
    display_name: str
    topology: str
    description: Optional[str] = None
    has_ihx: bool = Field(False, description="Has internal heat exchanger")
    has_economizer: bool = Field(False, description="Has economizer")
    supported_econ_types: Optional[List[str]] = Field(None, description="Supported economizer types")
    is_transcritical: bool = Field(False, description="Supports transcritical operation")


class ModelList(BaseModel):
    """List of available heat pump models."""

    models: List[ModelInfo]
    total_count: int


class ParameterInfo(BaseModel):
    """Default parameters for a specific model."""

    model_name: str
    econ_type: Optional[str] = None
    parameters: Dict[str, Any]


class RefrigerantList(BaseModel):
    """List of supported refrigerants."""

    refrigerants: List[str]
    total_count: int


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    status_code: int
