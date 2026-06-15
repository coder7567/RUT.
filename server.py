#!/usr/bin/env python3
"""
RUT_TRAILBLAZER API Server
FastAPI application that exposes RUT routing, bailout, community, convoy, emergency, vehicle, and subscription features to clients.
"""

import os
import sys
import logging
from typing import Tuple, Dict, Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles

# Ensure routing_engine module can be imported from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routing_engine.router import RUTRouter
from database import engine, Base, SessionLocal
from models import User
import community_routes
import convoy_ws
import emergency_routes
import vehicle_routes
import monetization_routes

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RUT_API_Server")

# Define Pydantic request models for validation
class RouteRequest(BaseModel):
    start_coord: Tuple[float, float] = Field(
        ..., 
        description="Starting coordinates as (longitude, latitude)",
        example=(-105.1234, 39.5678)
    )
    end_coord: Tuple[float, float] = Field(
        ..., 
        description="Ending coordinates as (longitude, latitude)",
        example=(-105.5678, 39.1234)
    )
    unorthodoxy_score: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Shortcut slider value: 0.0 (Standard) to 1.0 (Extreme Off-road)"
    )

class BailoutRequest(BaseModel):
    current_coord: Tuple[float, float] = Field(
        ..., 
        description="Current GPS coordinates as (longitude, latitude)",
        example=(-105.3456, 39.3456)
    )

# Initialize FastAPI App
app = FastAPI(
    title="RUT TrailBlazer API",
    description="Backend routing, community, convoy, emergency, vehicle, and subscription service for off-road GPS navigation adventure paths.",
    version="2.0.0",
    docs_url=None,
    redoc_url=None
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

# Global router instance
router = RUTRouter()

# Include Routers
app.include_router(community_routes.router)
app.include_router(convoy_ws.router)
app.include_router(emergency_routes.router)
app.include_router(vehicle_routes.router)
app.include_router(monetization_routes.router)

@app.on_event("startup")
def startup_event():
    """
    Load GIS processed map data and build database tables on server startup.
    """
    # Auto-generate SQLite tables if not present
    logger.info("Initializing relational database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        
        # Seed default user User-1 if it does not exist to unify user identity across layers
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == "User-1").first()
            if not user:
                logger.info("Seeding default user User-1...")
                new_user = User(
                    id="User-1",
                    username="TrailBlazerOne",
                    email="one@rut-trailblazer.com",
                    xp_points=1200,
                    reputation_score=45,
                    is_pro=True
                )
                db.add(new_user)
                db.commit()
                logger.info("Default user User-1 seeded successfully.")
        except Exception as seed_err:
            logger.error(f"Error seeding default user: {seed_err}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    logger.info(
        f"SKIP_MAP_LOAD raw value = {repr(os.getenv('SKIP_MAP_LOAD'))}"
    )

    if os.getenv("SKIP_MAP_LOAD", "").strip() == "1":
        logger.warning("Bypassing GIS map loading for rapid development mode.")
        return

    # Default path to unified output GeoJSON from GIS pipeline or customized via env
    geojson_path = os.getenv(
        "MAP_PATH",
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../data-pipeline/output.geojson")
        )
    )
    
    logger.info(f"Checking for GIS map data at: {geojson_path}")
    if os.path.exists(geojson_path):
        try:
            router.load_geojson(geojson_path)
            logger.info("Successfully loaded GIS map data into active routing graph.")
        except Exception as e:
            logger.error(f"Error loading GIS map data on startup: {e}")
    else:
        logger.warning(
            f"GIS map data file not found at {geojson_path}. "
            "Please run gis_processor.py to generate it. Routing engine is starting empty."
        )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, str]:
    """
    Basic service health check endpoint.
    """
    nodes_count = len(router.vertices) if router.is_loaded else 0
    edges_count = len(router.edges) if router.is_loaded else 0
    return {
        "status": "healthy",
        "loaded_nodes": str(nodes_count),
        "loaded_edges": str(edges_count)
    }

@app.post("/api/route", status_code=status.HTTP_200_OK)
def get_route(payload: RouteRequest) -> Dict[str, Any]:
    """
    Calculates off-road, adventure route based on unorthodoxy score settings.
    Runs synchronously (offloaded to FastAPI worker threads) to prevent blocking the event loop.
    """
    if not router.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Routing graph is currently empty. No GIS data is loaded."
        )

    try:
        res = router.calculate_route(
            start=payload.start_coord,
            end=payload.end_coord,
            unorthodoxy_score=payload.unorthodoxy_score
        )

        if res.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("message", "Route calculation failed.")
            )

        return res
    finally:
        # Explicit C-allocation cleanup to release lazy incidence list view immediately after returning data
        router.cleanup()

@app.post("/api/bailout", status_code=status.HTTP_200_OK)
def trigger_bailout(payload: BailoutRequest) -> Dict[str, Any]:
    """
    Calculates physical shortest route to nearest paved highway.
    """
    if not router.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Routing graph is currently empty. No GIS data is loaded."
        )

    res = router.bail_out(current_coord=payload.current_coord)

    if res.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Bailout path calculation failed.")
        )

    return res
