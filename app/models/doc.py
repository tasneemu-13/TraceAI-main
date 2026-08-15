from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from app.database import Base

class InvestigationDoc(Base):
    """
    Holds documents parsed into the FAISS vector store for Case RAG.
    """
    __tablename__ = "investigation_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(36), nullable=False, index=True)
    doc_type = Column(String(64), nullable=False)  # Note, Statement, Report, Email, History
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # Store author, location, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SightingMatch(Base):
    """
    Saves AI detection results so officers can approve or reject them.
    """
    __tablename__ = "sighting_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(36), nullable=False, index=True)
    submission_id = Column(String(36), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)  # Distance or percentage
    confidence = Column(Float, nullable=False)  # Derived confidence score (e.g. 0 to 100)
    status = Column(String(16), default="Pending", nullable=False)  # Pending, Approved, Rejected
    reviewed_by = Column(String(64), nullable=True)  # Username of reviewer
    reviewed_on = Column(DateTime, nullable=True)
    comments = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
