import os
import json
import base64
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.repositories import case as case_repo
from app.repositories import doc as doc_repo
from app.repositories import submission as sub_repo
from app.models.case import RegisteredCases
from app.models.doc import InvestigationDoc, SightingMatch
from app.models.submission import PublicSubmissions
from app.services import matching as match_service
from app.services import age_progression as age_service
from app.services import rag as rag_service
from app.services import report as report_service
from app.services import notification as notify_service
from app.config import settings

router = APIRouter(prefix="/api/cases", tags=["Cases"])

class NoteCreate(BaseModel):
    content: str
    doc_type: str = "Officer Note"  # Officer Note, Witness Statement, Sighting Report, Case Update, Evidence
    title: Optional[str] = "Case Note Update"

class MatchReview(BaseModel):
    status: str  # Approved, Rejected
    comments: Optional[str] = None
    officer_name: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_case(
    name: str = Form(...),
    age: str = Form(...),
    complainant_name: str = Form(...),
    last_seen: str = Form(...),
    address: str = Form(...),
    submitted_by: str = Form(...),  # Officer username
    father_name: Optional[str] = Form(None),
    complainant_mobile: Optional[str] = Form(None),
    complainant_email: Optional[str] = Form(None),
    adhaar_card: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    birth_marks: Optional[str] = Form(None),
    medical_info: Optional[str] = Form(None),
    languages_spoken: Optional[str] = Form(None),
    physical_description: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    case_id = str(uuid4())
    
    # Save original photo to disk
    original_filename = f"{case_id}_orig.jpg"
    original_path = os.path.join(settings.UPLOAD_DIR, original_filename)
    
    try:
        content = await photo.read()
        with open(original_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded photo: {e}")

    # Extract Face Mesh Landmarks from original photo
    img_cv = cv2 = None
    try:
        # Load image via cv2
        import cv2
        img_cv = cv2.imread(original_path)
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        landmarks = match_service.extract_face_mesh_from_frame(img_rgb)
    except Exception as e:
        # Clean up file
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(status_code=400, detail=f"Failed to analyze face in image: {e}")

    if not landmarks:
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(
            status_code=400, 
            detail="No face detected in the photo. Please upload a clear portrait."
        )

    # Generate Age Progression Appearance
    progressed_filename = f"{case_id}_prog.jpg"
    progressed_path, progressed_landmarks = age_service.generate_age_progression(original_path, progressed_filename)

    # Save case in database
    new_case = RegisteredCases(
        id=case_id,
        submitted_by=submitted_by,
        name=name,
        father_name=father_name,
        age=age,
        complainant_name=complainant_name,
        complainant_mobile=complainant_mobile,
        complainant_email=complainant_email,
        adhaar_card=adhaar_card,
        last_seen=last_seen,
        address=address,
        city=city or "Unknown",
        description=description,
        face_mesh=json.dumps(landmarks),
        status="NF",
        birth_marks=birth_marks,
        original_image_path=original_path,
        age_progressed_image_path=progressed_path,
        age_progressed_face_mesh=progressed_landmarks,
        medical_info=medical_info,
        languages_spoken=languages_spoken,
        physical_description=physical_description
    )
    
    case_repo.create_case(db, new_case)
    
    # Trigger matching pipeline asynchronously (or inline for MVP execution)
    match_service.run_face_matching(db)

    return {
        "message": "Case registered successfully with face encoding and age progression.",
        "case_id": case_id,
        "age_progressed_image": progressed_path
    }

@router.get("/")
def get_cases(status: str = "All", submitted_by: str = None, db: Session = Depends(get_db)):
    cases = case_repo.list_cases(db, status=status, submitted_by=submitted_by)
    return cases

@router.get("/{case_id}")
def get_case_details(case_id: str, db: Session = Depends(get_db)):
    case = case_repo.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    # Get associated notes, matches
    notes = doc_repo.get_docs_by_case(db, case_id)
    matches = sub_repo.get_sighting_matches_by_case(db, case_id)
    timeline = rag_service.rag_assistant.generate_investigation_timeline(db, case_id)
    
    match_details = []
    for m in matches:
        sub = sub_repo.get_submission_by_id(db, m.submission_id)
        if sub:
            match_details.append({
                "match_id": m.id,
                "submission_id": sub.id,
                "submitted_by": sub.submitted_by or "Anonymous",
                "location": sub.location,
                "mobile": sub.mobile,
                "submitted_on": sub.submitted_on,
                "similarity_score": m.similarity_score,
                "confidence": m.confidence,
                "status": m.status,
                "image_path": sub.image_path,
                "comments": m.comments
            })
            
    return {
        "case": case,
        "notes": notes,
        "matches": match_details,
        "timeline": timeline
    }

@router.post("/{case_id}/notes")
def add_case_note(case_id: str, note: NoteCreate, db: Session = Depends(get_db)):
    case = case_repo.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    new_doc = InvestigationDoc(
        case_id=case_id,
        doc_type=note.doc_type,
        title=note.title,
        content=note.content
    )
    doc_repo.create_doc(db, new_doc)
    
    # Sync RAG store
    rag_service.rag_assistant.reindex_all_docs(db)
    
    return {"message": "Document logged and vectorized for case."}

@router.get("/{case_id}/report", response_class=HTMLResponse)
def get_case_report(case_id: str, db: Session = Depends(get_db)):
    html_report = report_service.generate_case_summary_html(db, case_id)
    return html_report

@router.post("/matches/{match_id}/review")
def review_match(match_id: int, req: MatchReview, db: Session = Depends(get_db)):
    match = sub_repo.get_sighting_match(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match record not found.")
        
    sub_repo.update_sighting_match_status(
        db, 
        match_id=match_id, 
        status=req.status, 
        reviewed_by=req.officer_name, 
        comments=req.comments
    )
    
    case = case_repo.get_case_by_id(db, match.case_id)
    
    if req.status == "Approved":
        # Update case found status and matched submission ID
        case_repo.update_case(db, match.case_id, {"status": "F", "matched_with": match.submission_id})
        # Mark submission status resolved
        sub_repo.get_submission_by_id(db, match.submission_id).status = "F"
        db.commit()
        
        # Trigger notification
        notify_service.notify_complainant_of_match(
            complainant_name=case.complainant_name,
            complainant_email=case.complainant_email,
            complainant_mobile=case.complainant_mobile,
            case_name=case.name,
            similarity=match.confidence
        )
        
    return {"message": f"Match status successfully updated to {req.status}."}

@router.get("/{case_id}/photo/original")
def get_original_photo(case_id: str, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    case = case_repo.get_case_by_id(db, case_id)
    if not case or not case.original_image_path or not os.path.exists(case.original_image_path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(case.original_image_path, media_type="image/jpeg")

@router.get("/{case_id}/photo/progressed")
def get_progressed_photo(case_id: str, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    case = case_repo.get_case_by_id(db, case_id)
    if not case or not case.age_progressed_image_path or not os.path.exists(case.age_progressed_image_path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(case.age_progressed_image_path, media_type="image/jpeg")
