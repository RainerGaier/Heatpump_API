"""
Simulation endpoints for running heat pump calculations.

This module provides endpoints for:
- Design point simulation
- Off-design simulation
- Part-load characteristics
- Asynchronous simulation with background tasks
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Optional, Dict, Any
import logging

from heatpumps.api.schemas import (
    SimulationRequest,
    SimulationResult,
    DetailedSimulationResult,
    TaskResponse,
    AsyncSimulationRequest,
    PartloadResult,
    PartloadPoint,
    OffdesignResult,
    OffdesignPoint,
)
from heatpumps.api.dependencies import get_simulation_service
from heatpumps.api.workers import run_simulation_task
from heatpumps.simulation import run_design
from heatpumps.parameters import get_params
from heatpumps.variables import hp_model_classes

logger = logging.getLogger(__name__)
router = APIRouter()


def deep_merge_params(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge parameter dictionaries.

    This ensures nested dicts like params['ihx'] are merged rather than replaced,
    allowing partial parameter overrides while preserving defaults.
    """
    result = defaults.copy()

    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge_params(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


@router.post(
    "/design",
    response_model=SimulationResult,
    status_code=status.HTTP_200_OK,
    summary="Run design point simulation",
    description="Execute a steady-state design point simulation for the specified heat pump model.",
)
async def simulate_design(request: SimulationRequest) -> SimulationResult:
    """
    Run a design point simulation synchronously.

    Args:
        request: Simulation configuration including model name, parameters, and options

    Returns:
        SimulationResult with COP, efficiency, and power values

    Raises:
        HTTPException: If model not found or simulation fails
    """
    try:
        # Validate model exists
        if request.model_name not in hp_model_classes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model_name}' not found. Use /api/v1/models to list available models.",
            )

        # Get default parameters and merge with request params
        try:
            # Get the class object and its name for get_params()
            model_class = hp_model_classes[request.model_name]
            class_name = model_class.__name__
            default_params = get_params(class_name, request.econ_type)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model parameters not found for '{request.model_name}'",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load parameters: {str(e)}",
            )

        # Deep merge user params with defaults to preserve nested dicts
        params = deep_merge_params(default_params, request.params)

        # Run simulation
        logger.info(f"Starting design simulation for model: {request.model_name}")
        hp = run_design(request.model_name, params)

        # Extract results
        result = SimulationResult(
            model_name=request.model_name,
            converged=hp.solved_design,
            cop=hp.cop if hp.solved_design else None,
            epsilon=hp.epsilon if hp.solved_design and hasattr(hp, "epsilon") else None,
            heat_output=hp.buses["heat output"].P.val if hp.solved_design else None,
            power_input=hp.buses["power input"].P.val if hp.solved_design else None,
            cost_total=None,  # TODO: Implement cost calculation extraction
            error_message=None if hp.solved_design else "Simulation did not converge",
        )

        if not hp.solved_design:
            logger.warning(f"Simulation for {request.model_name} did not converge")
            result.error_message = "Simulation did not converge. Try adjusting parameters."

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )


@router.post(
    "/design/detailed",
    response_model=DetailedSimulationResult,
    status_code=status.HTTP_200_OK,
    summary="Run design point simulation with detailed results",
    description="Execute simulation and return full state point data and exergy analysis.",
)
async def simulate_design_detailed(request: SimulationRequest) -> DetailedSimulationResult:
    """
    Run a design point simulation with detailed thermodynamic data.

    Returns full state points, exergy analysis, and component data.
    """
    # TODO: Implement detailed result extraction
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Detailed simulation results not yet implemented",
    )


@router.post(
    "/offdesign",
    response_model=OffdesignResult,
    status_code=status.HTTP_200_OK,
    summary="Run off-design simulation",
    description="Execute off-design simulation over a range of operating conditions with full temperature sweep.",
)
async def simulate_offdesign(request: SimulationRequest) -> OffdesignResult:
    """
    Run off-design simulation sweep.

    This endpoint performs a comprehensive off-design analysis:
    1. Runs design point simulation
    2. Sweeps through heat source temperature range
    3. Sweeps through heat sink temperature range
    4. Sweeps through part-load ratios
    5. Returns all operating points with COP, heat output, and power

    Temperature ranges and part-load ratios can be customized via offdesign_config.
    """
    try:
        # Validate model exists
        if request.model_name not in hp_model_classes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model_name}' not found. Use /api/v1/models to list available models.",
            )

        # Get default parameters and merge with request params
        try:
            model_class = hp_model_classes[request.model_name]
            class_name = model_class.__name__
            default_params = get_params(class_name, request.econ_type)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load parameters: {str(e)}",
            )

        # Deep merge user params with defaults to preserve nested dicts
        params = deep_merge_params(default_params, request.params)

        # Apply custom off-design configuration if provided
        if request.offdesign_config:
            logger.info("Applying custom off-design configuration")
            # Ensure offdesign dict exists (should already from defaults)
            if 'offdesign' not in params:
                params['offdesign'] = {'save_results': True}

            # Configure heat source temperature range
            if request.offdesign_config.heat_source_range:
                hs_range = request.offdesign_config.heat_source_range
                if not hs_range.constant:
                    logger.info(f"Heat source range: {hs_range.start}°C to {hs_range.end}°C")
                    params['offdesign']['T_hs_ff_start'] = hs_range.start
                    params['offdesign']['T_hs_ff_end'] = hs_range.end
                    if hs_range.steps is not None:
                        params['offdesign']['T_hs_ff_steps'] = hs_range.steps
                else:
                    # Constant temperature - use design point value
                    design_T_hs = params.get('T_hs_ff', params.get('ambient', {}).get('T', 10.0))
                    params['offdesign']['T_hs_ff_start'] = design_T_hs
                    params['offdesign']['T_hs_ff_end'] = design_T_hs
                    params['offdesign']['T_hs_ff_steps'] = 1

            # Configure heat sink temperature range
            if request.offdesign_config.heat_sink_range:
                cons_range = request.offdesign_config.heat_sink_range
                if not cons_range.constant:
                    logger.info(f"Heat sink range: {cons_range.start}°C to {cons_range.end}°C")
                    params['offdesign']['T_cons_ff_start'] = cons_range.start
                    params['offdesign']['T_cons_ff_end'] = cons_range.end
                    if cons_range.steps is not None:
                        params['offdesign']['T_cons_ff_steps'] = cons_range.steps
                else:
                    # Constant temperature - use design point value
                    design_T_cons = params.get('T_cons_ff', params.get('B1', {}).get('T', 35.0))
                    params['offdesign']['T_cons_ff_start'] = design_T_cons
                    params['offdesign']['T_cons_ff_end'] = design_T_cons
                    params['offdesign']['T_cons_ff_steps'] = 1

            # Configure part-load range
            if request.offdesign_config.partload_range:
                pl_config = request.offdesign_config.partload_range
                logger.info(f"Part-load range: {pl_config.min_ratio} to {pl_config.max_ratio}")
                params['offdesign']['partload_min'] = pl_config.min_ratio
                params['offdesign']['partload_max'] = pl_config.max_ratio
                if pl_config.steps is not None:
                    params['offdesign']['partload_steps'] = pl_config.steps

        # Run design simulation first
        logger.info(f"Starting off-design simulation for model: {request.model_name}")
        logger.info("Step 1: Running design point simulation...")
        hp = run_design(request.model_name, params)

        if not hp.solved_design:
            logger.warning(f"Design simulation for {request.model_name} did not converge")
            return OffdesignResult(
                model_name=request.model_name,
                converged=False,
                total_points=0,
                converged_points=0,
                error_message="Design point simulation did not converge. Cannot proceed with off-design analysis.",
            )

        # Store design point results
        design_cop = hp.cop
        design_heat_output = hp.buses["heat output"].P.val

        logger.info(f"Step 2: Running off-design simulation sweep...")
        # Run off-design simulation
        try:
            hp.offdesign_simulation(log_simulations=False)
        except Exception as e:
            logger.error(f"Off-design simulation failed: {str(e)}", exc_info=True)
            return OffdesignResult(
                model_name=request.model_name,
                converged=False,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                total_points=0,
                converged_points=0,
                error_message=f"Off-design simulation failed: {str(e)}",
            )

        logger.info(f"Step 3: Extracting off-design results...")
        # Extract all operating points from the results DataFrame
        try:
            results_df = hp.results_offdesign if hasattr(hp, 'results_offdesign') else None

            if results_df is None or results_df.empty:
                logger.warning("Off-design results are empty")
                return OffdesignResult(
                    model_name=request.model_name,
                    converged=False,
                    design_cop=design_cop,
                    design_heat_output=design_heat_output,
                    total_points=0,
                    converged_points=0,
                    error_message="No off-design results generated.",
                )

            # Extract temperature and part-load ranges
            T_hs_range = hp.T_hs_ff_range.tolist() if hasattr(hp, 'T_hs_ff_range') else []
            T_cons_range = hp.T_cons_ff_range.tolist() if hasattr(hp, 'T_cons_ff_range') else []
            pl_range = hp.pl_range.tolist() if hasattr(hp, 'pl_range') else []

            # Iterate through all operating points
            operating_points = []
            converged_count = 0

            for T_hs_ff in T_hs_range:
                for T_cons_ff in T_cons_range:
                    for pl_ratio in pl_range:
                        try:
                            # Access the specific result from the MultiIndex DataFrame
                            result_row = results_df.loc[(T_hs_ff, T_cons_ff, pl_ratio)]

                            # Check convergence
                            converged = result_row.get('residual', 1.0) < 1e-3 if 'residual' in result_row else True

                            if converged:
                                converged_count += 1

                            point = OffdesignPoint(
                                T_hs_ff=float(T_hs_ff),
                                T_cons_ff=float(T_cons_ff),
                                partload_ratio=float(pl_ratio),
                                cop=float(result_row['COP']) if converged and result_row['COP'] is not None else None,
                                heat_output=float(result_row['Q']) if converged and result_row['Q'] is not None else None,
                                power_input=float(result_row['P']) if converged and result_row['P'] is not None else None,
                                epsilon=float(result_row['epsilon']) if converged and 'epsilon' in result_row and result_row['epsilon'] is not None else None,
                                converged=converged,
                            )
                            operating_points.append(point)

                        except (KeyError, IndexError) as e:
                            logger.warning(f"Could not extract point ({T_hs_ff}, {T_cons_ff}, {pl_ratio}): {e}")
                            continue
                        except Exception as e:
                            logger.warning(f"Error processing point ({T_hs_ff}, {T_cons_ff}, {pl_ratio}): {e}")
                            continue

            logger.info(f"Off-design simulation complete: {converged_count}/{len(operating_points)} points converged")

            return OffdesignResult(
                model_name=request.model_name,
                converged=True,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                temperature_range={
                    "T_hs_ff": T_hs_range,
                    "T_cons_ff": T_cons_range,
                },
                partload_range=pl_range,
                operating_points=operating_points,
                total_points=len(operating_points),
                converged_points=converged_count,
            )

        except Exception as e:
            logger.error(f"Off-design result extraction failed: {str(e)}", exc_info=True)
            return OffdesignResult(
                model_name=request.model_name,
                converged=False,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                total_points=0,
                converged_points=0,
                error_message=f"Off-design result extraction failed: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Off-design simulation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Off-design simulation failed: {str(e)}",
        )


@router.post(
    "/partload",
    response_model=PartloadResult,
    status_code=status.HTTP_200_OK,
    summary="Run part-load characteristics simulation",
    description="Calculate part-load performance characteristics at different load ratios.",
)
async def simulate_partload(request: SimulationRequest) -> PartloadResult:
    """
    Run part-load characteristics simulation.

    This endpoint:
    1. Runs design point simulation first
    2. Performs off-design simulation across part-load range
    3. Returns COP, heat output, and power input at each load ratio

    The simulation varies the heat pump capacity from minimum to maximum load
    to characterize real-world performance.
    """
    try:
        # Validate model exists
        if request.model_name not in hp_model_classes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model_name}' not found. Use /api/v1/models to list available models.",
            )

        # Get default parameters and merge with request params
        try:
            model_class = hp_model_classes[request.model_name]
            class_name = model_class.__name__
            default_params = get_params(class_name, request.econ_type)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load parameters: {str(e)}",
            )

        # Deep merge user params with defaults to preserve nested dicts
        params = deep_merge_params(default_params, request.params)

        # Apply custom part-load configuration if provided
        if request.partload_config:
            logger.info(f"Applying custom part-load configuration: min={request.partload_config.min_ratio}, max={request.partload_config.max_ratio}")
            # Ensure offdesign dict exists (should already from defaults)
            if 'offdesign' not in params:
                params['offdesign'] = {'save_results': True}
            params['offdesign']['partload_min'] = request.partload_config.min_ratio
            params['offdesign']['partload_max'] = request.partload_config.max_ratio
            if request.partload_config.steps is not None:
                params['offdesign']['partload_steps'] = request.partload_config.steps

        # Run design simulation first
        logger.info(f"Starting part-load simulation for model: {request.model_name}")
        logger.info("Step 1: Running design point simulation...")
        hp = run_design(request.model_name, params)

        if not hp.solved_design:
            logger.warning(f"Design simulation for {request.model_name} did not converge")
            return PartloadResult(
                model_name=request.model_name,
                converged=False,
                total_points=0,
                converged_points=0,
                error_message="Design point simulation did not converge. Cannot proceed with part-load analysis.",
            )

        # Store design point results
        design_cop = hp.cop
        design_heat_output = hp.buses["heat output"].P.val

        logger.info(f"Step 2: Running off-design simulation...")
        # Run off-design simulation (required for part-load)
        try:
            hp.offdesign_simulation(log_simulations=False)
        except Exception as e:
            logger.error(f"Off-design simulation failed: {str(e)}", exc_info=True)
            return PartloadResult(
                model_name=request.model_name,
                converged=False,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                total_points=0,
                converged_points=0,
                error_message=f"Off-design simulation failed: {str(e)}",
            )

        logger.info(f"Step 3: Calculating part-load characteristics...")
        # Calculate part-load characteristics
        # This accesses the results from offdesign_simulation stored in hp
        try:
            # The offdesign_simulation populates arrays needed by calc_partload_char
            # Extract the part-load range that was simulated
            if not hasattr(hp, 'pl_range'):
                logger.warning("No part-load range found after off-design simulation")
                return PartloadResult(
                    model_name=request.model_name,
                    converged=False,
                    design_cop=design_cop,
                    design_heat_output=design_heat_output,
                    total_points=0,
                    converged_points=0,
                    error_message="Part-load range not generated. Check offdesign parameters.",
                )

            # Access the offdesign results DataFrame
            results_df = hp.results_offdesign if hasattr(hp, 'results_offdesign') else None

            if results_df is None or results_df.empty:
                logger.warning("Off-design results are empty")
                return PartloadResult(
                    model_name=request.model_name,
                    converged=False,
                    design_cop=design_cop,
                    design_heat_output=design_heat_output,
                    total_points=0,
                    converged_points=0,
                    error_message="No off-design results generated.",
                )

            # Extract part-load points at design temperatures
            # Filter results for design point temperatures
            design_T_hs = params.get('T_hs_ff', hp.params['ambient']['T'])
            design_T_cons = params.get('T_cons_ff', hp.params['B1']['T'])

            # Get results for all part-load ratios at design temperatures
            partload_points = []
            converged_count = 0

            for pl_ratio in hp.pl_range:
                try:
                    # Access the specific result from the MultiIndex DataFrame
                    result_row = results_df.loc[(design_T_hs, design_T_cons, pl_ratio)]

                    converged = result_row.get('residual', 1.0) < 1e-3 if 'residual' in result_row else True

                    if converged:
                        converged_count += 1

                    point = PartloadPoint(
                        load_ratio=float(pl_ratio),
                        cop=float(result_row['COP']) if converged and result_row['COP'] is not None else None,
                        heat_output=float(result_row['Q']) if converged and result_row['Q'] is not None else None,
                        power_input=float(result_row['P']) if converged and result_row['P'] is not None else None,
                        epsilon=float(result_row['epsilon']) if converged and 'epsilon' in result_row and result_row['epsilon'] is not None else None,
                        converged=converged,
                    )
                    partload_points.append(point)

                except (KeyError, IndexError) as e:
                    logger.warning(f"Could not extract part-load point for ratio {pl_ratio}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing part-load point {pl_ratio}: {e}")
                    continue

            logger.info(f"Part-load simulation complete: {converged_count}/{len(partload_points)} points converged")

            return PartloadResult(
                model_name=request.model_name,
                converged=True,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                partload_points=partload_points,
                total_points=len(partload_points),
                converged_points=converged_count,
            )

        except Exception as e:
            logger.error(f"Part-load calculation failed: {str(e)}", exc_info=True)
            return PartloadResult(
                model_name=request.model_name,
                converged=False,
                design_cop=design_cop,
                design_heat_output=design_heat_output,
                total_points=0,
                converged_points=0,
                error_message=f"Part-load calculation failed: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Part-load simulation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Part-load simulation failed: {str(e)}",
        )


@router.post(
    "/async",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit asynchronous simulation",
    description="Submit a simulation to run in the background. Returns task ID for status tracking.",
)
async def simulate_async(
    request: AsyncSimulationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit a simulation task to run asynchronously.

    Returns immediately with a task ID that can be used to check status.
    Optionally sends results to a webhook URL when complete.
    """
    # TODO: Implement async task submission with proper task queue (Celery/RQ)
    # For now, using FastAPI BackgroundTasks as placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Async simulation not yet implemented. Use synchronous /design endpoint.",
    )
