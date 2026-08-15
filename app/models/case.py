from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text
from app.database import Base

class RegisteredCases(Base):
    __tablename__ = "registeredcases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False)
    submitted_by = Column(String(64), nullable=False)  # Username of the officer who registered it
    name = Column(String(128), nullable=False)
    father_name = Column(String(128), nullable=True)
    age = Column(String(8), nullable=True)
    complainant_name = Column(String(128), nullable=False)
    complainant_mobile = Column(String(10), nullable=True)
    complainant_email = Column(String(128), nullable=True)
    adhaar_card = Column(String(12), nullable=True)
    last_seen = Column(String(64), nullable=False)
    address = Column(String(512), nullable=False)
    city = Column(String(64), nullable=True)
    description = Column(String(1024), nullable=True)
    face_mesh = Column(Text, nullable=False)  # JSON string of 1404 landmark coordinates
    submitted_on = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(16), default="NF", nullable=False)  # "F" (Found) or "NF" (Not Found)
    birth_marks = Column(String(512), nullable=True)
    matched_with = Column(String(36), nullable=True)  # ID of matching public submission
    
    # Extended fields
    original_image_path = Column(String(255), nullable=True)
    age_progressed_image_path = Column(String(255), nullable=True)
    age_progressed_face_mesh = Column(Text, nullable=True)  # JSON string of 1404 landmark coordinates
    medical_info = Column(String(512), nullable=True)
    languages_spoken = Column(String(128), nullable=True)
    physical_description = Column(String(512), nullable=True)
