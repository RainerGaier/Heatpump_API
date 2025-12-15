"""
Reports API routes for saving and retrieving simulation reports.

This module provides endpoints for:
- Saving simulation reports to Cloud Storage
- Retrieving reports by ID
- Deleting reports
- Listing available reports
- Viewing reports as HTML
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status, Request
from heatpumps.api.schemas import (
    SaveReportRequest,
    SaveReportResponse,
    ReportInfo,
    ErrorResponse
)
from heatpumps.api.config import Settings, get_settings
from heatpumps.api.services.storage import StorageService

logger = logging.getLogger(__name__)

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
router = APIRouter()

# Initialize Jinja2 templates
template_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))


def load_refrigerant_database() -> dict:
    """
    Load refrigerant properties database from static files.

    Returns:
        Dictionary of refrigerant properties
    """
    try:
        static_path = Path(__file__).parent.parent.parent / "static"
        refrigerants_file = static_path / "refrigerants.json"

        if refrigerants_file.exists():
            with open(refrigerants_file) as f:
                return json.load(f)
        else:
            logger.warning(f"Refrigerants database not found at {refrigerants_file}")
            return {}
    except Exception as e:
        logger.error(f"Failed to load refrigerant database: {e}")
        return {}




def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    """
    Dependency for getting storage service instance.

    Args:
        settings: Application settings

    Returns:
        Initialized StorageService

    Raises:
        HTTPException: If storage service cannot be initialized
    """
    try:
        # Check if GCS is configured
        if not settings.GCP_PROJECT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloud Storage not configured. Please set GCP_PROJECT_ID environment variable."
            )

        if not settings.GCS_BUCKET_NAME:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cloud Storage bucket not configured. Please set GCS_BUCKET_NAME environment variable."
            )

        return StorageService(
            bucket_name=settings.GCS_BUCKET_NAME,
            project_id=settings.GCP_PROJECT_ID,
            location=settings.GCS_LOCATION
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize storage service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service initialization failed: {str(e)}"
        )


@router.post(
    "/save",
    response_model=SaveReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save simulation report",
    description="Save a simulation report to Cloud Storage and get a shareable URL",
    responses={
        201: {"description": "Report saved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def save_report(
    request: SaveReportRequest,
    storage: StorageService = Depends(get_storage_service)
) -> SaveReportResponse:
    """
    Save a simulation report to Cloud Storage.

    This endpoint:
    1. Receives simulation data and metadata
    2. Uploads to Google Cloud Storage as JSON
    3. Generates a signed URL (valid for 7 days)
    4. Returns URLs and expiration info

    Args:
        request: Report data including simulation results and metadata
        storage: Storage service dependency

    Returns:
        SaveReportResponse with URLs and expiration

    Raises:
        HTTPException: If save operation fails
    """
    try:
        logger.info(f"Saving report {request.metadata.report_id}")

        # Combine metadata and simulation data for storage
        full_report_data = {
            "metadata": request.metadata.model_dump(),
            **request.simulation_data
        }

        # Upload to Cloud Storage
        result = await storage.upload_json(
            data=full_report_data,
            report_id=request.metadata.report_id
        )

        # Calculate expiration time (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)

        return SaveReportResponse(
            report_id=request.metadata.report_id,
            storage_url=result["storage_url"],
            signed_url=result["signed_url"],
            expires_at=expires_at.isoformat() + "Z",
            message="Report saved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to save report {request.metadata.report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save report: {str(e)}"
        )


@router.get(
    "/{report_id}",
    response_model=Dict[str, Any],
    summary="Get simulation report",
    description="Retrieve a simulation report by ID from Cloud Storage",
    responses={
        200: {"description": "Report retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def get_report(
    report_id: str,
    storage: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """
    Retrieve a simulation report from Cloud Storage.

    Args:
        report_id: Unique report identifier
        storage: Storage service dependency

    Returns:
        Complete report data as JSON

    Raises:
        HTTPException: If report not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving report {report_id}")

        data = await storage.download_json(report_id=report_id)
        return data

    except FileNotFoundError:
        logger.warning(f"Report {report_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@router.get(
    "/{report_id}/view",
    response_class=HTMLResponse,
    summary="View simulation report as HTML",
    description="Render HTML view of simulation report matching Streamlit UI",
    responses={
        200: {"description": "HTML report rendered successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def view_report_html(
    report_id: str,
    request: Request,
    storage: StorageService = Depends(get_storage_service)
):
    """
    Render HTML view of a simulation report.

    Returns HTML page with:
    - Configuration results metrics
    - Topology & Refrigerant info
    - State variables table
    - Economic evaluation
    - Exergy assessment with Sankey diagram

    Args:
        report_id: Unique report identifier
        request: FastAPI request object (for template context)
        storage: Storage service dependency

    Returns:
        HTML page rendered from template

    Raises:
        HTTPException: If report not found or rendering fails
    """
    try:
        logger.info(f"Rendering HTML view for report {report_id}")

        # Download report JSON from Cloud Storage
        report_data = await storage.download_json(report_id=report_id)

        # Load refrigerant database for properties table
        refrigerants = load_refrigerant_database()

        # Prepare template context
        context = {
            "request": request,
            "report_id": report_id,
            "report_data": report_data,
            "refrigerants": refrigerants,
        }

        return templates.TemplateResponse("report.html", context)

    except FileNotFoundError:
        logger.warning(f"Report {report_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    except Exception as e:
        logger.error(f"Error rendering report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render report: {str(e)}"
        )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete simulation report",
    description="Delete a simulation report from Cloud Storage",
    responses={
        204: {"description": "Report deleted successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def delete_report(
    report_id: str,
    storage: StorageService = Depends(get_storage_service)
):
    """
    Delete a simulation report from Cloud Storage.

    Args:
        report_id: Unique report identifier
        storage: Storage service dependency

    Raises:
        HTTPException: If report not found or deletion fails
    """
    try:
        logger.info(f"Deleting report {report_id}")

        deleted = await storage.delete_report(report_id=report_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[ReportInfo],
    summary="List simulation reports",
    description="List available simulation reports in Cloud Storage",
    responses={
        200: {"description": "Reports listed successfully"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def list_reports(
    limit: int = 100,
    storage: StorageService = Depends(get_storage_service)
) -> List[ReportInfo]:
    """
    List available simulation reports.

    Args:
        limit: Maximum number of reports to return (default: 100)
        storage: Storage service dependency

    Returns:
        List of report information

    Raises:
        HTTPException: If listing fails
    """
    try:
        logger.info(f"Listing reports (limit: {limit})")

        reports = await storage.list_reports(limit=limit)

        return [ReportInfo(**report) for report in reports]

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}"
        )


@router.get(
    "/{report_id}/url",
    response_model=Dict[str, str],
    summary="Get signed URL for report",
    description="Generate a new signed URL for accessing a report",
    responses={
        200: {"description": "Signed URL generated successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
        503: {"model": ErrorResponse, "description": "Storage service unavailable"}
    }
)
async def get_signed_url(
    report_id: str,
    expiration_days: int = 7,
    storage: StorageService = Depends(get_storage_service)
) -> Dict[str, str]:
    """
    Generate a new signed URL for a report.

    Args:
        report_id: Unique report identifier
        expiration_days: Number of days until URL expires (default: 7, max: 30)
        storage: Storage service dependency

    Returns:
        Dictionary with signed_url and expires_at

    Raises:
        HTTPException: If report not found or URL generation fails
    """
    try:
        # Limit expiration to 30 days
        expiration_days = min(expiration_days, 30)

        logger.info(f"Generating signed URL for report {report_id} (expires in {expiration_days} days)")

        signed_url = await storage.get_signed_url(
            report_id=report_id,
            expiration_days=expiration_days
        )

        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        return {
            "signed_url": signed_url,
            "expires_at": expires_at.isoformat() + "Z"
        }

    except FileNotFoundError:
        logger.warning(f"Report {report_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL for report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate signed URL: {str(e)}"
        )
