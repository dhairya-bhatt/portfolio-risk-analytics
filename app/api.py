"""FastAPI application entrypoint and healthcheck endpoint."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import check_db_connection, get_db

settings = get_settings()

app = FastAPI(
    title="Portfolio Risk Analytics API",
    description=(
        "Microservice for storing ETF price series, modeling portfolios, "
        "and computing institutional risk analytics."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class HealthResponse(BaseModel):
    """Health check payload validating API status and database connectivity."""

    status: str
    database: str
    app: str
    version: str


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Validates app responsiveness and database round-trip connectivity.",
    tags=["Health"],
)
def health_check(
    db: Annotated[Session, Depends(get_db)],
) -> HealthResponse:
    """Check both the API container and a live database round-trip (SELECT 1)."""
    db_ok = check_db_connection(db)
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "app": "portfolio-risk-analytics",
                "version": "0.1.0",
            },
        )

    return HealthResponse(
        status="healthy",
        database="connected",
        app="portfolio-risk-analytics",
        version="0.1.0",
    )
