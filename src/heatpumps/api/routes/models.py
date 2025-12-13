"""
Model information endpoints.

This module provides endpoints for:
- Listing available heat pump models
- Getting model details and capabilities
- Retrieving default parameters for models
- Listing supported refrigerants
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging

from heatpumps.api.schemas import (
    ModelInfo,
    ModelList,
    ParameterInfo,
    RefrigerantList,
)
from heatpumps.parameters import get_params
from heatpumps.variables import hp_models, hp_model_classes

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=ModelList,
    summary="List all available models",
    description="Get a list of all heat pump models available for simulation.",
)
async def list_models() -> ModelList:
    """
    List all available heat pump models.

    Returns information about each model including topology, features, and capabilities.
    """
    try:
        models_info = []

        for model_key, model_data in hp_models.items():
            # Determine economizer support
            econ_types = None
            if "econ" in model_data.get("base_topology", ""):
                econ_types = ["closed", "open", "closed_ihx", "open_ihx"]

            model_info = ModelInfo(
                name=model_key,  # Use the actual key from hp_models
                display_name=model_data.get("display_name", model_key),
                topology=model_data.get("base_topology", "unknown"),
                description=None,  # TODO: Add descriptions to variables.py
                has_ihx=model_data.get("nr_ihx", 0) > 0,
                has_economizer="econ" in model_data.get("base_topology", ""),
                supported_econ_types=econ_types,
                is_transcritical=model_data.get("trans", False) if "trans" in model_key else False,
            )
            models_info.append(model_info)

        return ModelList(
            models=models_info,
            total_count=len(models_info),
        )

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get(
    "/{model_name}",
    response_model=ModelInfo,
    summary="Get model details",
    description="Get detailed information about a specific heat pump model.",
)
async def get_model_info(model_name: str) -> ModelInfo:
    """
    Get detailed information about a specific model.

    Args:
        model_name: Name of the heat pump model (use the model key, e.g., 'simple', 'ihx', 'econ_closed')

    Returns:
        ModelInfo with model details

    Raises:
        HTTPException: If model not found
    """
    try:
        # Look up model in hp_models dictionary using the key
        if model_name not in hp_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found. Use /api/v1/models to list available models.",
            )

        model_data = hp_models[model_name]

        # Determine economizer support
        econ_types = None
        if "econ" in model_data.get("base_topology", ""):
            econ_types = ["closed", "open", "closed_ihx", "open_ihx"]

        return ModelInfo(
            name=model_name,
            display_name=model_data.get("display_name", model_name),
            topology=model_data.get("base_topology", "unknown"),
            description=None,
            has_ihx=model_data.get("nr_ihx", 0) > 0,
            has_economizer="econ" in model_data.get("base_topology", ""),
            supported_econ_types=econ_types,
            is_transcritical=model_data.get("trans", False) if "trans" in model_name else False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}",
        )


@router.get(
    "/{model_name}/parameters",
    response_model=ParameterInfo,
    summary="Get default parameters",
    description="Get default simulation parameters for a specific model.",
)
async def get_model_parameters(
    model_name: str,
    econ_type: Optional[str] = None,
) -> ParameterInfo:
    """
    Get default parameters for a model.

    Args:
        model_name: Name of the heat pump model
        econ_type: Optional economizer type (for economizer models)

    Returns:
        ParameterInfo with default parameters

    Raises:
        HTTPException: If model not found or parameters cannot be loaded
    """
    try:
        # Validate model exists
        if model_name not in hp_model_classes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found",
            )

        # Get parameters - need to convert model key to class name
        try:
            model_class = hp_model_classes[model_name]
            class_name = model_class.__name__
            params = get_params(class_name, econ_type)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load parameters: {str(e)}",
            )

        return ParameterInfo(
            model_name=model_name,
            econ_type=econ_type,
            parameters=params,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parameters: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get parameters: {str(e)}",
        )


@router.get(
    "/refrigerants/list",
    response_model=RefrigerantList,
    summary="List supported refrigerants",
    description="Get a list of all refrigerants supported by the simulator.",
)
async def list_refrigerants() -> RefrigerantList:
    """
    List all supported refrigerants.

    Returns refrigerants that are supported by CoolProp and have diagram data available.
    """
    try:
        # TODO: Dynamically query available refrigerants from CoolProp
        # and cross-reference with diagram JSON files
        # For now, return common refrigerants
        common_refrigerants = [
            "R717",      # Ammonia
            "R1234yf",
            "R1234ze(E)",
            "R134a",
            "R744",      # CO2
            "R290",      # Propane
            "R600a",     # Isobutane
            "R410A",
            "R407C",
            "R32",
        ]

        return RefrigerantList(
            refrigerants=sorted(common_refrigerants),
            total_count=len(common_refrigerants),
        )

    except Exception as e:
        logger.error(f"Error listing refrigerants: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list refrigerants: {str(e)}",
        )
