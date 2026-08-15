from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(16), default="Public", nullable=False)  # Admin, Officer, Public
    name = Column(String(128), nullable=True)
    city = Column(String(64), nullable=True)
    area = Column(String(128), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_secret = Column(String(64), nullable=True)  # Secret seed for OTP verification
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
