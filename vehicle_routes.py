#!/usr/bin/env encoding
# -*- coding: utf-8 -*-
"""
RUT_TRAILBLAZER Vehicle Profiles API
Validates vehicle capabilities against encountered route obstacles and hazards.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models import VehicleProfile, ObstacleType

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

class RouteCheckRequest(BaseModel):
    vehicle_id: int = Field(..., description="ID of the vehicle profile to evaluate")
    obstacles: List[ObstacleType] = Field(..., description="List of obstacles present on the route")

@router.post("/check-route", status_code=status.HTTP_200_OK)
def check_route_compatibility(payload: RouteCheckRequest, db: Session = Depends(get_db)):
    """
    T3.5: Compares vehicle attributes against route obstacles.
    Returns list of warnings if vehicle capabilities are exceeded.
    """
    vehicle = db.query(VehicleProfile).filter(VehicleProfile.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle profile with ID {payload.vehicle_id} not found."
        )

    warnings = []
    is_compatible = True

    # Capability checking logic loop
    for obstacle in payload.obstacles:
        if obstacle == ObstacleType.FLOODED_CROSSING:
            if not vehicle.has_snorkel:
                is_compatible = False
                warnings.append(
                    "CRITICAL WARNING: Route contains a 'Flooded Crossing'. "
                    "Your vehicle lacks a Snorkel. Do not cross to avoid engine hydro-locking!"
                )
        
        elif obstacle == ObstacleType.DEEP_MUD:
            if not (vehicle.has_winch or vehicle.has_tow_straps or vehicle.clearance_level >= 3):
                is_compatible = False
                warnings.append(
                    "WARNING: Route contains 'Deep Mud'. Your vehicle lacks recovery equipment "
                    "(Winch/Tow Straps) and has low clearance. High risk of getting stuck."
                )
        
        elif obstacle == ObstacleType.WASHED_OUT:
            if vehicle.clearance_level < 3:
                is_compatible = False
                warnings.append(
                    f"WARNING: Route contains a 'Washed Out' section. Your clearance level ({vehicle.clearance_level}) "
                    "is below the recommended clearance level (3+)."
                )

    return {
        "status": "success",
        "vehicle_name": vehicle.vehicle_name,
        "is_compatible": is_compatible,
        "warnings": warnings,
        "checked_obstacles_count": len(payload.obstacles)
    }
