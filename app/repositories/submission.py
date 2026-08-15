from sqlalchemy.orm import Session
from datetime import datetime
from app.models.submission import PublicSubmissions
from app.models.doc import SightingMatch

def get_submission_by_id(db: Session, sub_id: str) -> PublicSubmissions:
    return db.query(PublicSubmissions).filter(PublicSubmissions.id == sub_id).first()

def create_submission(db: Session, submission: PublicSubmissions) -> PublicSubmissions:
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

def list_submissions(db: Session, status: str = None):
    query = db.query(PublicSubmissions)
    if status:
        query = query.filter(PublicSubmissions.status == status)
    return query.all()

# Sighting matches CRUD
def create_sighting_match(db: Session, match: SightingMatch) -> SightingMatch:
    db.add(match)
    db.commit()
    db.refresh(match)
    return match

def get_sighting_match(db: Session, match_id: int) -> SightingMatch:
    return db.query(SightingMatch).filter(SightingMatch.id == match_id).first()

def get_sighting_matches_by_case(db: Session, case_id: str):
    return db.query(SightingMatch).filter(SightingMatch.case_id == case_id).all()

def get_sighting_matches_by_submission(db: Session, sub_id: str):
    return db.query(SightingMatch).filter(SightingMatch.submission_id == sub_id).all()

def get_pending_matches(db: Session):
    return db.query(SightingMatch).filter(SightingMatch.status == "Pending").all()

def update_sighting_match_status(db: Session, match_id: int, status: str, reviewed_by: str, comments: str = None) -> SightingMatch:
    match = get_sighting_match(db, match_id)
    if match:
        match.status = status
        match.reviewed_by = reviewed_by
        match.reviewed_on = datetime.utcnow()
        match.comments = comments
        db.commit()
        db.refresh(match)
    return match
