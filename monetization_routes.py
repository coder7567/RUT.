#!/usr/bin/env encoding
# -*- coding: utf-8 -*-
"""
RUT_TRAILBLAZER Monetization & Offline Maps API
Handles Pro subscription upgrades and gated MBTiles offline region downloads.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models import User

router = APIRouter(prefix="/api/subscription", tags=["Monetization"])

class UpgradeRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user upgrading to Pro")
    card_mock_token: str = Field("tok_visa", description="Mock payment gateway gateway token")

@router.post("/upgrade", status_code=status.HTTP_200_OK)
def upgrade_user_to_pro(payload: UpgradeRequest, db: Session = Depends(get_db)):
    """
    T4.2: Simulates payment processing and upgrades a user account to 'Pro' status.
    """
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.user_id} not found."
        )

    # Mock payment processing
    if not payload.card_mock_token.startswith("tok_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment processing failed: Invalid card transaction token."
        )

    # Set user to Pro status
    user.is_pro = True
    db.commit()
    db.refresh(user)

    return {
        "status": "upgrade_success",
        "message": f"User '{user.username}' successfully upgraded to Pro plan.",
        "is_pro": user.is_pro
    }

@router.get("/maps/offline/{region_id}", status_code=status.HTTP_200_OK)
def download_offline_map(region_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    T4.2: Gated endpoint verifying Pro membership before allowing .mbtiles package retrieval.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    # Verify Pro membership
    if not user.is_pro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Offline map packages are exclusive to RUT Pro subscribers."
        )

    # Simulates returning the pre-packaged .mbtiles file from data-pipeline
    return {
        "status": "download_authorized",
        "region_id": region_id,
        "mbtiles_package_name": f"{region_id}_trails.mbtiles",
        "download_url": f"https://api.rut-trailblazer.com/downloads/maps/{region_id}.mbtiles"
    }
