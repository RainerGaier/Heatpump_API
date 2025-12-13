"""
Background worker functions for asynchronous simulation tasks.

This module provides worker functions that can be executed by:
- FastAPI BackgroundTasks (simple, same-process)
- Celery (distributed task queue, recommended for production)
- Redis Queue (RQ) (lightweight alternative to Celery)

TODO: Implement proper task queue with Celery or RQ for production use.
"""

import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def run_simulation_task(
    task_id: str,
    model_name: str,
    params: Dict[str, Any],
    econ_type: Optional[str] = None,
    webhook_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a simulation task in the background.

    This function can be called by FastAPI BackgroundTasks or a task queue worker.

    Args:
        task_id: Unique task identifier
        model_name: Name of heat pump model to simulate
        params: Simulation parameters
        econ_type: Optional economizer type
        webhook_url: Optional URL to POST results when complete

    Returns:
        Dictionary with simulation results

    TODO: Integrate with Celery/RQ for proper async execution
    """
    logger.info(f"Starting background simulation task {task_id} for model {model_name}")

    try:
        from heatpumps.simulation import run_design
        from heatpumps.parameters import get_params

        # Get default parameters and merge
        default_params = get_params(model_name, econ_type)
        merged_params = {**default_params, **params}

        # Run simulation
        hp = run_design(model_name, merged_params)

        # Extract results
        result = {
            "task_id": task_id,
            "model_name": model_name,
            "converged": hp.solved_design,
            "cop": hp.cop if hp.solved_design else None,
            "epsilon": hp.epsilon if hp.solved_design and hasattr(hp, "epsilon") else None,
            "heat_output": hp.buses["heat output"].P.val if hp.solved_design else None,
            "power_input": hp.buses["power input"].P.val if hp.solved_design else None,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Task {task_id} completed successfully. COP: {result['cop']}")

        # Send webhook if URL provided
        if webhook_url:
            send_webhook(webhook_url, result)

        return result

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        error_result = {
            "task_id": task_id,
            "model_name": model_name,
            "converged": False,
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }

        if webhook_url:
            send_webhook(webhook_url, error_result)

        return error_result


def send_webhook(url: str, payload: Dict[str, Any]):
    """
    Send results to a webhook URL.

    Args:
        url: Webhook URL to POST results to
        payload: Results data to send
    """
    try:
        import httpx

        logger.info(f"Sending webhook to {url}")
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Webhook sent successfully. Status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to send webhook to {url}: {str(e)}")
        # Don't raise - webhook failure shouldn't fail the task


# Celery configuration (for future implementation)
# Uncomment and configure when ready to use Celery
"""
from celery import Celery

# Initialize Celery app
celery_app = Celery(
    "heatpump_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="simulate_heatpump")
def simulate_heatpump_celery(
    task_id: str,
    model_name: str,
    params: Dict[str, Any],
    econ_type: Optional[str] = None,
    webhook_url: Optional[str] = None,
):
    # Celery task wrapper for run_simulation_task
    return run_simulation_task(task_id, model_name, params, econ_type, webhook_url)
"""
