#!/usr/bin/env python3
"""
RUT_TRAILBLAZER Community Routes
API endpoints for trail submissions, votes/verification, condition reports, social feed, and comments.
"""

import enum
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models import User, TrailSubmission, ConditionReport, ObstacleType, Comment

router = APIRouter(prefix="/api/community", tags=["Community"])

# --- PYDANTIC SCHEMAS ---

class VoteType(str, enum.Enum):
    UP = "up"
    DOWN = "down"

class TrailSubmitRequest(BaseModel):
    submitter_id: str = Field(..., description="ID of the user submitting the trail")
    geojson_trace_data: str = Field(..., description="Raw GeoJSON string of the route track")

class VoteRequest(BaseModel):
    vote_type: VoteType = Field(..., description="Vote action: 'up' or 'down'")

class ConditionReportRequest(BaseModel):
    reporter_id: str = Field(..., description="ID of the user reporting the condition")
    obstacle_type: ObstacleType = Field(..., description="Type of obstacle encountered")
    latitude: float = Field(..., description="Latitude of the obstacle")
    longitude: float = Field(..., description="Longitude of the obstacle")

class CommentCreateRequest(BaseModel):
    author_id: str = Field(..., description="ID of the user posting the comment")
    text: str = Field(..., description="Comment content text")

# --- API ENDPOINTS ---

@router.post("/trails/submit", status_code=status.HTTP_201_CREATED)
def submit_trail(payload: TrailSubmitRequest, db: Session = Depends(get_db)):
    """
    T2.2: Submits a new off-road trail GPS trace.
    Initializes status as 'pending'.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == payload.submitter_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.submitter_id} not found."
        )

    new_submission = TrailSubmission(
        submitter_id=payload.submitter_id,
        geojson_trace_data=payload.geojson_trace_data,
        upvotes=0,
        downvotes=0,
        status="pending"
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return {
        "status": "success",
        "message": "Trail submitted successfully and is pending community verification.",
        "trail_id": new_submission.id,
        "submission_status": new_submission.status
    }

@router.post("/trails/{trail_id}/vote", status_code=status.HTTP_200_OK)
def vote_trail(trail_id: int, payload: VoteRequest, db: Session = Depends(get_db)):
    """
    T2.3: Upvotes or downvotes a pending trail.
    If upvotes reach 3, the trail is promoted to 'verified'.
    """
    trail = db.query(TrailSubmission).filter(TrailSubmission.id == trail_id).first()
    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trail submission with ID {trail_id} not found."
        )

    if payload.vote_type == VoteType.UP:
        trail.upvotes += 1
    else:
        trail.downvotes += 1

    # Logic Hook: Automatically verify when upvotes reach 3
    if trail.upvotes >= 3 and trail.status != "verified":
        trail.status = "verified"
        submitter = db.query(User).filter(User.id == trail.submitter_id).first()
        if submitter:
            submitter.xp_points += 100  # Bonus XP for verified trail
            submitter.reputation_score += 10

    db.commit()
    db.refresh(trail)

    return {
        "status": "success",
        "trail_id": trail.id,
        "upvotes": trail.upvotes,
        "downvotes": trail.downvotes,
        "submission_status": trail.status
    }

@router.post("/conditions/report", status_code=status.HTTP_201_CREATED)
def report_condition(payload: ConditionReportRequest, db: Session = Depends(get_db)):
    """
    T2.4: Submits a real-time hazard/condition report.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == payload.reporter_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.reporter_id} not found."
        )

    new_report = ConditionReport(
        reporter_id=payload.reporter_id,
        obstacle_type=payload.obstacle_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        active_status=True
    )

    user.xp_points += 25
    user.reputation_score += 2

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "status": "success",
        "message": f"Hazard report '{payload.obstacle_type.value}' successfully registered.",
        "report_id": new_report.id,
        "active_status": new_report.active_status
    }

@router.get("/feed", status_code=status.HTTP_200_OK)
def get_feed(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    T2.5: Retrieves a combined chronological feed of active Condition Reports
    and verified Trail Submissions with pagination.
    """
    reports = db.query(ConditionReport).filter(ConditionReport.active_status == True).all()
    trails = db.query(TrailSubmission).filter(TrailSubmission.status == "verified").all()

    feed_items = []

    # Map reports to standardized feed dictionaries
    for r in reports:
        feed_items.append({
            "type": "condition_report",
            "id": r.id,
            "reporter_id": r.reporter_id,
            "obstacle_type": r.obstacle_type.value,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "timestamp": r.timestamp
        })

    # Map verified trails to standardized feed dictionaries
    for t in trails:
        feed_items.append({
            "type": "trail_submission",
            "id": t.id,
            "submitter_id": t.submitter_id,
            "geojson_trace_data": t.geojson_trace_data,
            "upvotes": t.upvotes,
            "downvotes": t.downvotes,
            "timestamp": t.timestamp
        })

    # Sort combined feed chronologically descending (newest first)
    feed_items.sort(key=lambda x: x["timestamp"], reverse=True)

    # Apply pagination bounds
    paginated_feed = feed_items[skip : skip + limit]
    return paginated_feed

@router.post("/trails/{trail_id}/comments", status_code=status.HTTP_201_CREATED)
def post_comment(trail_id: int, payload: CommentCreateRequest, db: Session = Depends(get_db)):
    """
    T2.5: Allows posting a comment on a specific trail submission.
    """
    # Verify trail exists
    trail = db.query(TrailSubmission).filter(TrailSubmission.id == trail_id).first()
    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trail submission with ID {trail_id} not found."
        )

    # Verify user exists
    user = db.query(User).filter(User.id == payload.author_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.author_id} not found."
        )

    new_comment = Comment(
        author_id=payload.author_id,
        trail_id=trail_id,
        text=payload.text
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {
        "status": "success",
        "comment_id": new_comment.id,
        "author_id": new_comment.author_id,
        "trail_id": new_comment.trail_id,
        "text": new_comment.text,
        "timestamp": new_comment.timestamp
    }
