#!/usr/bin/env encoding
# -*- coding: utf-8 -*-
"""
RUT_TRAILBLAZER Emergency Beacon API
Generates compressed SOS satellite payloads for offline Garmin/Helium transmission.
"""

import struct
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models import User

logger = logging.getLogger("RUT_Emergency_Beacon")

router = APIRouter(prefix="/api/emergency", tags=["Emergency"])

class BeaconRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user triggering distress")
    latitude: float = Field(..., description="Current latitude")
    longitude: float = Field(..., description="Current longitude")
    distress_msg: str = Field("SOS", description="Distress message details (truncated to 16 chars offline)")

@router.post("/beacon", status_code=status.HTTP_201_CREATED)
def trigger_beacon(payload: BeaconRequest, db: Session = Depends(get_db)):
    """
    T3.4: Generates a compressed satellite/Helium network transmission string.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.user_id} not found."
        )

    # 1. Generate compressed transmission string
    # Structure: [User ID (4-byte uint)][Latitude (4-byte float)][Longitude (4-byte float)][Msg (16-byte char)]
    msg_bytes = payload.distress_msg.encode("utf-8")[:16].ljust(16, b"\x00")
    try:
        # Extract numeric suffix from user_id string for binary spec compatibility (e.g. "User-1" -> 1)
        numeric_id = 1
        import re
        match = re.search(r'\d+', payload.user_id)
        if match:
            numeric_id = int(match.group())
            
        binary_packet = struct.pack("!Iff16s", numeric_id, payload.latitude, payload.longitude, msg_bytes)
        compressed_payload = base64.b64encode(binary_packet).decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile compressed distress packet: {e}"
        )

    # 2. Console SOS Broadcast Log
    logger.critical(
        f"\n==================================================\n"
        f"!!! EMERGENCY BEACON RECEIVED !!!\n"
        f"USER ID: {payload.user_id} ({user.username})\n"
        f"COORDINATES: {payload.latitude}, {payload.longitude}\n"
        f"MESSAGE: {payload.distress_msg}\n"
        f"PACKET: {compressed_payload}\n"
        f"=================================================="
    )

    return {
        "status": "SOS_BROADCAST_SENT",
        "raw_packet": compressed_payload,
        "payload_bytes_size": len(binary_packet),
        "data": {
            "user_id": payload.user_id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "distress_msg": payload.distress_msg
        }
    }
