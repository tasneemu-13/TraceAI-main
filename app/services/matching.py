import os
import json
import urllib.request
import numpy as np
import cv2
import PIL.Image
from collections import defaultdict
from sqlalchemy.orm import Session
from sklearn.neighbors import KNeighborsClassifier
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from app.config import settings
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions
from app.models.doc import SightingMatch

_MODEL_PATH = settings.MEDIAPIPE_MODEL_PATH
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

def _ensure_model_silent():
    if not os.path.exists(_MODEL_PATH):
        print("[Face Match] Downloading MediaPipe model...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)

def _build_detector(num_faces: int = 5):
    _ensure_model_silent()
    base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=num_faces,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)

def _normalize_image(image: np.ndarray) -> np.ndarray:
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    elif image.shape[2] == 4:
        image = image[:, :, :3]
    return image

def normalize_landmarks(landmarks: list) -> list:
    """
    Normalize 3D landmarks:
    1. Center the face by translating the nose tip (landmark 4) to (0, 0, 0).
    2. Scale the face by dividing by the distance between outer eye corners (landmark 33 and 263).
    """
    try:
        pts = np.array(landmarks).reshape(-1, 3)
        nose_tip = pts[4]
        pts = pts - nose_tip
        eye_distance = np.linalg.norm(pts[33] - pts[263])
        if eye_distance > 0:
            pts = pts / eye_distance
        return pts.flatten().tolist()
    except Exception as e:
        print(f"[Face Normalization Error] Failed: {e}")
        return landmarks

def extract_face_mesh_from_frame(frame_rgb: np.ndarray) -> list | None:
    """
    Extract face mesh landmarks (1404 coordinates) for exactly one face.
    """
    _ensure_model_silent()
    frame_rgb = _normalize_image(frame_rgb)
    try:
        detector = _build_detector(num_faces=1)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = detector.detect(mp_image)
        detector.close()
        if result.face_landmarks:
            lm_list = result.face_landmarks[0]
            raw_lms = [coord for lm in lm_list for coord in (lm.x, lm.y, lm.z)]
            return normalize_landmarks(raw_lms)
        return None
    except Exception as e:
        print(f"[Face Match Error] Landmark extraction failed: {e}")
        return None

def extract_unique_faces_from_video(video_path: str, frame_interval: int = 15, similarity_threshold: float = 0.05):
    """
    Extract unique face landmarks from video frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    def cosine_distance(a, b):
        a, b = np.array(a), np.array(b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 1.0
        return 1.0 - float(np.dot(a, b) / denom)

    unique_faces = []
    frame_idx = 0
    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            landmarks = extract_face_mesh_from_frame(frame_rgb)
            if landmarks is not None:
                is_duplicate = any(
                    cosine_distance(landmarks, ex_lm) < similarity_threshold
                    for ex_lm, _ in unique_faces
                )
                if not is_duplicate:
                    unique_faces.append((landmarks, frame_rgb))
        frame_idx += 1
    cap.release()
    return unique_faces

def run_face_matching(db: Session, distance_threshold: float = 3.0) -> dict:
    """
    Matches public submissions against registered cases using the KNN pipeline.
    Supports matching against both original and age progressed face meshes.
    """
    # Fetch not found registered cases and public submissions
    registered_cases = db.query(RegisteredCases).filter(RegisteredCases.status == "NF").all()
    public_submissions = db.query(PublicSubmissions).filter(PublicSubmissions.status == "NF").all()

    if not registered_cases or not public_submissions:
        return {"status": False, "message": "No cases or public submissions to match."}

    # Prepare features and labels
    reg_features = []
    reg_labels = []  # Map index in reg_features to case ID

    for case in registered_cases:
        try:
            landmarks = json.loads(case.face_mesh)
            if landmarks and len(landmarks) >= 1404:
                reg_features.append(landmarks[:1404])
                reg_labels.append(case.id)
            
            # Check for age progressed mesh
            if case.age_progressed_face_mesh:
                prog_landmarks = json.loads(case.age_progressed_face_mesh)
                if prog_landmarks and len(prog_landmarks) >= 1404:
                    reg_features.append(prog_landmarks[:1404])
                    reg_labels.append(case.id)
        except Exception:
            continue

    if not reg_features:
        return {"status": False, "message": "No valid registered face features found."}

    reg_features = np.array(reg_features).astype(float)
    numeric_labels = list(range(len(reg_features)))

    # Fit KNN classifier
    knn = KNeighborsClassifier(n_neighbors=1, algorithm="ball_tree", weights="distance")
    knn.fit(reg_features, numeric_labels)

    matched_count = 0
    new_matches = []

    # Predict for each public submission
    for pub in public_submissions:
        try:
            pub_l = json.loads(pub.face_mesh)
            if not pub_l or len(pub_l) < 1404:
                continue
            pub_landmarks = np.array(pub_l[:1404]).astype(float)

            closest_distances, indices = knn.kneighbors([pub_landmarks])
            closest_distance = float(closest_distances[0][0])
            predicted_idx = int(indices[0][0])
            case_id = reg_labels[predicted_idx]
            print(f"[Match Engine] KNN Distance: {closest_distance:.4f} between Case {case_id} and Sighting {pub.id} (Threshold: {distance_threshold})")

            if closest_distance <= distance_threshold:
                case_id = reg_labels[predicted_idx]
                
                # Check if this match was already recorded to avoid duplicates
                existing = db.query(SightingMatch).filter(
                    SightingMatch.case_id == case_id,
                    SightingMatch.submission_id == pub.id
                ).first()

                if not existing:
                    # Calculate similarity score (closer to 0 is better, convert to % score)
                    # For KNN distance, 0 is 100% match. Threshold 3.0 means 3.0 distance -> 50% match
                    similarity_percentage = max(0.0, min(100.0, 100.0 - (closest_distance / distance_threshold) * 50.0))
                    confidence = similarity_percentage
                    
                    match_record = SightingMatch(
                        case_id=case_id,
                        submission_id=pub.id,
                        similarity_score=closest_distance,
                        confidence=confidence,
                        status="Pending"
                    )
                    db.add(match_record)
                    new_matches.append(match_record)
                    matched_count += 1
        except Exception as e:
            print(f"[Face Match Error] Sighting prediction error: {e}")
            continue

    if matched_count > 0:
        db.commit()

    return {"status": True, "matches_created": matched_count}
