from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from .database import Base
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# SQLAlchemy Models

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    severity = Column(String)  # high, medium, low
    source = Column(String)
    description = Column(Text)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="new")  # new, investigating, resolved

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    severity = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    artifacts = Column(JSON) # List of related alerts or evidence

# Pydantic Schemas

class AlertCreate(BaseModel):
    title: str
    severity: str
    source: str
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class AlertOut(AlertCreate):
    id: int
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str

class IncidentOut(IncidentCreate):
    id: int
    created_at: datetime
    status: str
    artifacts: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
