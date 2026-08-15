import os
import json
import tempfile
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.repositories import submission as sub_repo
from app.repositories import case as case_repo
from app.models.submission import PublicSubmissions
from app.services import matching as match_service
from app.config import settings

router = APIRouter(prefix="/api/submissions", tags=["Public Submissions"])

@router.post("/sighting", status_code=status.HTTP_201_CREATED)
async def submit_sighting(
    submitted_by: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    mobile: str = Form(...),
    email: Optional[str] = Form(None),
    birth_marks: Optional[str] = Form(None),
    is_anonymous: bool = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    sub_id = str(uuid4())
    filename = f"{sub_id}.jpg"
    dest_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save uploaded file
    try:
        content = await photo.read()
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Extract Face Mesh Landmarks
    try:
        import cv2
        img = cv2.imread(dest_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        landmarks = match_service.extract_face_mesh_from_frame(img_rgb)
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=f"Failed to analyze face mesh: {e}")

    if not landmarks:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=400, 
            detail="No face detected in the uploaded sighting photo. Please ensure the face is visible."
        )

    # Save to database
    new_submission = PublicSubmissions(
        id=sub_id,
        submitted_by=None if is_anonymous else submitted_by,
        face_mesh=json.dumps(landmarks),
        location=location,
        mobile=mobile,
        email=email,
        status="NF",
        birth_marks=birth_marks,
        image_path=dest_path,
        is_anonymous=is_anonymous,
        latitude=latitude,
        longitude=longitude,
        description=description,
        sighting_time=datetime.utcnow()
    )
    
    sub_repo.create_submission(db, new_submission)
    
    # Run the matching algorithm instantly to link the sighting
    match_service.run_face_matching(db)
    
    return {
        "message": "Sighting report submitted successfully. Officers will verify details shortly.",
        "submission_id": sub_id
    }

@router.post("/video-sighting", status_code=status.HTTP_201_CREATED)
async def submit_video_sighting(
    submitted_by: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    mobile: str = Form(...),
    email: Optional[str] = Form(None),
    birth_marks: Optional[str] = Form(None),
    is_anonymous: bool = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    video: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save video temporarily for OpenCV
    suffix = "." + video.filename.rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await video.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extract unique faces from video
        extracted_faces = match_service.extract_unique_faces_from_video(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract frames: {e}")
    finally:
        os.unlink(tmp_path)

    if not extracted_faces:
        raise HTTPException(status_code=400, detail="No faces detected in the video.")

    created_submissions = []
    
    # Register each face as a separate submission sighting
    for i, (landmarks, frame_rgb) in enumerate(extracted_faces):
        sub_id = str(uuid4())
        filename = f"{sub_id}_v{i}.jpg"
        dest_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save frame to disk
        import PIL.Image
        img = PIL.Image.fromarray(frame_rgb)
        img.save(dest_path)
        
        new_submission = PublicSubmissions(
            id=sub_id,
            submitted_by=None if is_anonymous else submitted_by,
            face_mesh=json.dumps(landmarks),
            location=location,
            mobile=mobile,
            email=email,
            status="NF",
            birth_marks=birth_marks,
            image_path=dest_path,
            is_anonymous=is_anonymous,
            latitude=latitude,
            longitude=longitude,
            description=description,
            sighting_time=datetime.utcnow()
        )
        sub_repo.create_submission(db, new_submission)
        created_submissions.append(sub_id)

    # Run the matching algorithm to generate matches
    match_service.run_face_matching(db)

    return {
        "message": f"Successfully processed video. Registered {len(created_submissions)} unique sightings.",
        "submission_ids": created_submissions
    }

@router.get("/track/{sub_id}")
def track_submission(sub_id: str, db: Session = Depends(get_db)):
    sub = sub_repo.get_submission_by_id(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Sighting submission not found.")
        
    # Get associated matches to see if approved
    matches = sub_repo.get_sighting_matches_by_submission(db, sub_id)
    
    verification_status = "Under Review"
    matched_case_name = None
    
    for m in matches:
        if m.status == "Approved":
            verification_status = "Verified"
            case = case_repo.get_case_by_id(db, m.case_id)
            if case:
                matched_case_name = case.name
        elif m.status == "Rejected" and verification_status != "Verified":
            verification_status = "Disproved"
            
    return {
        "submission_id": sub.id,
        "location": sub.location,
        "submitted_on": sub.submitted_on,
        "sighting_status": sub.status,  # NF = unresolved, F = verified/found
        "verification_status": verification_status,
        "matched_person": matched_case_name if verification_status == "Verified" else None
    }
