from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Boolean, Float
from app.database import Base

class PublicSubmissions(Base):
    __tablename__ = "publicsubmissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False)
    submitted_by = Column(String(128), nullable=True)  # Name of citizen (None if anonymous)
    face_mesh = Column(Text, nullable=False)  # JSON string of 1404 landmark coordinates
    location = Column(String(128), nullable=True)  # Location details
    mobile = Column(String(10), nullable=False)
    email = Column(String(64), nullable=True)
    status = Column(String(16), default="NF", nullable=False)  # "F" (Resolved/Found) or "NF" (Unresolved)
    birth_marks = Column(String(512), nullable=True)
    submitted_on = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Extended fields
    image_path = Column(String(255), nullable=True)
    video_path = Column(String(255), nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sighting_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String(1024), nullable=True)
