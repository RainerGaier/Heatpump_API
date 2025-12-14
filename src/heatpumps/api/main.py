"""
FastAPI application entry point for heatpump simulator API.

This module initializes the FastAPI application and registers all routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from heatpumps.api.routes import simulate, models, tasks, reports
from heatpumps.api.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Heatpump Simulator API",
    description="REST API for heat pump design and simulation calculations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simulate.router, prefix="/api/v1/simulate", tags=["Simulation"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Heatpump Simulator API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "heatpump-simulator-api",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


def run():
    """Entry point for running the API server."""
    import uvicorn

    uvicorn.run(
        "heatpumps.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run()
