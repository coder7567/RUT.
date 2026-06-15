#!/usr/bin/env python3
"""
RUT_TRAILBLAZER Database Models
Defines SQLAlchemy schemas for Users, Trail Submissions, Condition Reports, Comments, Challenge Points, and Vehicle Profiles.
"""

import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
from database import Base

class ObstacleType(str, enum.Enum):
    GATE_LOCKED = "Gate Locked"
    WASHED_OUT = "Washed Out"
    DEEP_MUD = "Deep Mud"
    FALLEN_TREE = "Fallen Tree"
    FLOODED_CROSSING = "Flooded Crossing"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    xp_points = Column(Integer, default=0, nullable=False)
    reputation_score = Column(Integer, default=0, nullable=False)
    is_pro = Column(Boolean, default=False, nullable=False)  # Monetization feature

    # Relationships
    submissions = relationship("TrailSubmission", back_populates="submitter")
    reports = relationship("ConditionReport", back_populates="reporter")
    comments = relationship("Comment", back_populates="author")
    challenge_points = relationship("ChallengePoint", back_populates="creator")
    vehicle_profiles = relationship("VehicleProfile", back_populates="owner")

class TrailSubmission(Base):
    __tablename__ = "trail_submissions"

    id = Column(Integer, primary_key=True, index=True)
    submitter_id = Column(String, ForeignKey("users.id"), nullable=False)
    geojson_trace_data = Column(Text, nullable=False)  # Raw GeoJSON string of the route
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    status = Column(String, default="pending", nullable=False)  # "pending" or "verified"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    submitter = relationship("User", back_populates="submissions")
    comments = relationship("Comment", back_populates="trail")

class ConditionReport(Base):
    __tablename__ = "condition_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(String, ForeignKey("users.id"), nullable=False)
    obstacle_type = Column(Enum(ObstacleType), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    active_status = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    reporter = relationship("User", back_populates="reports")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    trail_id = Column(Integer, ForeignKey("trail_submissions.id"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    author = relationship("User", back_populates="comments")
    trail = relationship("TrailSubmission", back_populates="comments")

class ChallengePoint(Base):
    __tablename__ = "challenge_points"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    creator = relationship("User", back_populates="challenge_points")

class VehicleProfile(Base):
    __tablename__ = "vehicle_profiles"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    vehicle_name = Column(String, nullable=False)
    clearance_level = Column(Integer, default=1, nullable=False)  # 1 to 5
    has_winch = Column(Boolean, default=False, nullable=False)
    has_tow_straps = Column(Boolean, default=False, nullable=False)
    has_snorkel = Column(Boolean, default=False, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="vehicle_profiles")
