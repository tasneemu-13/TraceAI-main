"""
Bulk upload script for seeding the production MySQL database.

Usage (run from project root):
    python scripts/bulk_upload.py                        
    python scripts/bulk_upload.py --officer <username>   # match your login username
"""

import argparse
import json
import os
import random
import sys
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Allow imports from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import PIL.Image
import numpy as np
import cv2

from app.database import db_session
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions
from app.services import matching as match_service
from app.services import age_progression as age_service
from app.config import settings

# Seed data lists
CITIES = [
    "Delhi", "Lucknow", "Kanpur", "Agra", "Meerut", "Varanasi",
    "Allahabad", "Mathura", "Bareilly", "Aligarh", "Moradabad",
    "Saharanpur", "Gorakhpur", "Firozabad", "Jhansi", "Noida",
    "Ghaziabad", "Faridabad", "Amritsar", "Ludhiana", "Jalandhar",
    "Chandigarh", "Dehradun", "Haridwar", "Rishikesh", "Shimla",
]

FIRST_NAMES_MALE = [
    "Anil", "Suresh", "Rajesh", "Ramesh", "Mahesh", "Dinesh", "Naresh",
    "Vikas", "Amit", "Deepak", "Rohit", "Mohit", "Sumit", "Sanjay",
    "Vijay", "Ajay", "Ravi", "Pavan", "Sachin", "Rahul", "Gaurav",
    "Nitin", "Pankaj", "Manish", "Rakesh", "Pradeep", "Hemant",
    "Vivek", "Arvind", "Harish",
]

FIRST_NAMES_FEMALE = [
    "Priya", "Sunita", "Geeta", "Seema", "Rekha", "Neha", "Pooja",
    "Kavita", "Anita", "Vandana", "Archana", "Sushma", "Meena",
    "Usha", "Asha", "Shweta", "Divya", "Nisha", "Sonia", "Ritu",
    "Poonam", "Anjali", "Sapna", "Komal", "Puja", "Swati",
]

LAST_NAMES = [
    "Sharma", "Gupta", "Singh", "Verma", "Yadav", "Mishra", "Tiwari",
    "Pandey", "Dubey", "Srivastava", "Chauhan", "Joshi", "Agarwal",
    "Bansal", "Garg", "Saxena", "Rastogi", "Chaudhary", "Shukla",
    "Tripathi", "Bajpai", "Gautam", "Kesarwani", "Awasthi",
]

AREAS = [
    "Sector {n} near main market",
    "near {landmark} railway station",
    "Civil Lines area",
    "{landmark} Chowk",
    "near {landmark} hospital",
    "Cantonment area",
    "near {landmark} bus stand",
    "old city area near {landmark} bazaar",
    "Model Town",
    "Gandhi Nagar",
    "Indira Nagar",
    "Rajiv Nagar",
    "Shastri Nagar",
    "Nehru Nagar",
    "Patel Nagar",
]

AREA_LANDMARKS = [
    "Central", "City", "New", "Old", "District", "Junction",
    "West", "East", "North", "South",
]

BIRTH_MARKS = [
    "Small mole on left cheek",
    "Scar on right forehead",
    "Dark birthmark near right ear",
    "Small scar below left eye",
    "Mole on chin",
    "Cut mark on left eyebrow",
    "Small mole on right cheek",
    "No visible markings",
]

DESCRIPTIONS = [
    "Was last seen wearing a blue kurta and dark trousers.",
    "Wearing school uniform — white shirt and navy blue trousers.",
    "Last seen in a red saree near the vegetable market.",
    "Was wearing jeans and a white t-shirt when last seen.",
    "Elderly person, wearing traditional dhoti and kurta.",
    "Teenager, medium height, last seen near the school gate.",
    "Was attending a wedding and went missing from the venue.",
    "Left home in the morning and did not return.",
    "Known to visit the nearby temple every morning.",
    "Works as a daily-wage labourer; did not return from worksite.",
]

def _random_name(gender: str = None) -> str:
    if gender == "female":
        first = random.choice(FIRST_NAMES_FEMALE)
    elif gender == "male":
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def _random_mobile() -> str:
    prefixes = ["98", "97", "96", "95", "94", "93", "80", "81", "70", "99"]
    return random.choice(prefixes) + str(random.randint(10000000, 99999999))

def _random_aadhaar() -> str:
    return str(random.randint(200000000000, 999999999999))

def _random_area(city: str) -> str:
    template = random.choice(AREAS)
    landmark = random.choice(AREA_LANDMARKS)
    n = random.randint(3, 25)
    return template.format(landmark=landmark, n=n) + f", {city}"

def _random_last_seen(city: str) -> str:
    days_ago = random.randint(1, 90)
    past_date = datetime.now() - timedelta(days=days_ago)
    date_str = past_date.strftime("%d %b %Y")
    area = _random_area(city)
    return f"{area} on {date_str}"

def _load_image_as_numpy(path: str) -> np.ndarray:
    img = PIL.Image.open(path).convert("RGB")
    return np.array(img)

def _image_files(folder: Path) -> list:
    exts = {".jpg", ".jpeg", ".png"}
    return [f for f in sorted(folder.iterdir()) if f.suffix.lower() in exts]

def upload_reported(folder: Path, officer: str = "officer") -> tuple[int, int]:
    files = _image_files(folder)
    if not files:
        print("  No image files found in reported/")
        return 0, 0

    ok = skip = 0
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    db = db_session()

    for img_path in files:
        print(f"  [{img_path.name}] ", end="", flush=True)
        try:
            image_np = _load_image_as_numpy(str(img_path))
            landmarks = match_service.extract_face_mesh_from_frame(image_np)
        except Exception as e:
            print(f"ERROR analyzing image: {e}")
            skip += 1
            continue

        if landmarks is None:
            print("no face detected — skipped")
            skip += 1
            continue

        case_id = str(uuid.uuid4())

        # Save original photo to settings.UPLOAD_DIR
        original_filename = f"{case_id}_orig.jpg"
        original_path = os.path.join(settings.UPLOAD_DIR, original_filename)
        try:
            PIL.Image.open(img_path).convert("RGB").save(original_path, "JPEG")
        except Exception as e:
            print(f"ERROR saving original image: {e}")
            skip += 1
            continue

        # Run age progression
        progressed_filename = f"{case_id}_prog.jpg"
        try:
            progressed_path, progressed_landmarks = age_service.generate_age_progression(original_path, progressed_filename)
        except Exception as e:
            print(f"Age progression failed: {e}. Seeding original landmarks as fallback.")
            progressed_path = None
            progressed_landmarks = None

        city = random.choice(CITIES)
        age = random.randint(5, 75)

        case = RegisteredCases(
            id=case_id,
            submitted_by=officer,
            name=_random_name(),
            father_name=_random_name(gender="male"),
            age=str(age),
            complainant_name=_random_name(),
            complainant_mobile=_random_mobile(),
            complainant_email=f"family_{case_id[:4]}@example.com",
            adhaar_card=_random_aadhaar(),
            last_seen=_random_last_seen(city),
            address=_random_area(city),
            city=city,
            description=random.choice(DESCRIPTIONS),
            face_mesh=json.dumps(landmarks),
            status="NF",
            birth_marks=random.choice(BIRTH_MARKS),
            original_image_path=original_path,
            age_progressed_image_path=progressed_path,
            age_progressed_face_mesh=progressed_landmarks,
            medical_info="No significant warnings logged.",
            languages_spoken="Hindi, English",
            physical_description="Medium built, dark hair."
        )

        try:
            db.add(case)
            db.commit()
            print(f"registered in MySQL as {case_id[:8]}…")
            ok += 1
        except Exception as e:
            db.rollback()
            print(f"DB ERROR: {e}")
            if os.path.exists(original_path):
                os.remove(original_path)
            if progressed_path and os.path.exists(progressed_path):
                os.remove(progressed_path)
            skip += 1

    db_session.remove()
    return ok, skip

def upload_publicly_seen(folder: Path) -> tuple[int, int]:
    files = _image_files(folder)
    if not files:
        print("  No image files found in publicly_seen/")
        return 0, 0

    ok = skip = 0
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    db = db_session()

    for img_path in files:
        print(f"  [{img_path.name}] ", end="", flush=True)
        try:
            image_np = _load_image_as_numpy(str(img_path))
            landmarks = match_service.extract_face_mesh_from_frame(image_np)
        except Exception as e:
            print(f"ERROR analyzing image: {e}")
            skip += 1
            continue

        if landmarks is None:
            print("no face detected — skipped")
            skip += 1
            continue

        sub_id = str(uuid.uuid4())

        # Save photo to settings.UPLOAD_DIR
        dest_path = os.path.join(settings.UPLOAD_DIR, f"{sub_id}.jpg")
        try:
            PIL.Image.open(img_path).convert("RGB").save(dest_path, "JPEG")
        except Exception as e:
            print(f"ERROR saving submission image: {e}")
            skip += 1
            continue

        city = random.choice(CITIES)

        submission = PublicSubmissions(
            id=sub_id,
            submitted_by=_random_name(),
            face_mesh=json.dumps(landmarks),
            location=_random_area(city),
            mobile=_random_mobile(),
            email=f"reporter_{sub_id[:4]}@example.com",
            status="NF",
            birth_marks=random.choice(BIRTH_MARKS),
            image_path=dest_path,
            is_anonymous=False,
            latitude=28.6139 + random.uniform(-0.1, 0.1),
            longitude=77.2090 + random.uniform(-0.1, 0.1),
            description="Spotted walking in target locality. Matches profile.",
            sighting_time=datetime.utcnow()
        )

        try:
            db.add(submission)
            db.commit()
            print(f"submitted in MySQL as {sub_id[:8]}…")
            ok += 1
        except Exception as e:
            db.rollback()
            print(f"DB ERROR: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            skip += 1

    db_session.remove()
    return ok, skip

def main():
    parser = argparse.ArgumentParser(description="Bulk upload images into the production MySQL database.")
    parser.add_argument(
        "--officer",
        default="officer",
        help="Login username to assign as submitted_by for reported cases (default: officer)",
    )
    args = parser.parse_args()

    bulk_dir = Path(__file__).parent / "bulk_data"
    reported_dir = bulk_dir / "reported"
    seen_dir = bulk_dir / "publicly_seen"

    print(f"\n=== Seeding MySQL — Reported Cases [officer: {args.officer}] ===")
    ok_r, skip_r = upload_reported(reported_dir, officer=args.officer)
    print(f"  Done: {ok_r} registered, {skip_r} skipped\n")

    print("=== Seeding MySQL — Public Sightings ===")
    ok_s, skip_s = upload_publicly_seen(seen_dir)
    print(f"  Done: {ok_s} submitted, {skip_s} skipped\n")

    # Run KNN matching automatically
    print("=== Executing Facial Recognition Matcher ===")
    db = db_session()
    try:
        match_res = match_service.run_face_matching(db)
        print(f"  Face recognition matching complete: {match_res.get('matches_created', 0)} new matches established.")
    except Exception as e:
        print(f"  Face recognition matcher error: {e}")
    finally:
        db_session.remove()

    total_ok = ok_r + ok_s
    total_skip = skip_r + skip_s
    print(f"\n=== Seeding Summary: {total_ok} uploaded, {total_skip} skipped ===\n")

if __name__ == "__main__":
    main()
