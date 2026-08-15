from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories import case as case_repo
from app.repositories import submission as sub_repo

router = APIRouter(prefix="/api/map", tags=["GIS Map"])

CITY_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Kanpur": (26.4499, 80.3319),
    "Nagpur": (21.1458, 79.0882),
    "Indore": (22.7196, 75.8577),
    "Bhopal": (23.2599, 77.4126),
    "Visakhapatnam": (17.6868, 83.2185),
    "Patna": (25.5941, 85.1376),
    "Vadodara": (22.3072, 73.1812),
    "Surat": (21.1702, 72.8311),
    "Noida": (28.5355, 77.3910),
    "Gurgaon": (28.4595, 77.0266),
    "Gurugram": (28.4595, 77.0266),
    "Chandigarh": (30.7333, 76.7794),
    "Coimbatore": (11.0168, 76.9558),
    "Kochi": (9.9312, 76.2673),
    "Agra": (27.1767, 78.0081),
    "Varanasi": (25.3176, 82.9739),
    "Meerut": (28.9845, 77.7064),
    "Raipur": (21.2514, 81.6296),
    "Ranchi": (23.3441, 85.3096),
    "Guwahati": (26.1445, 91.7362),
    "Jodhpur": (26.2389, 73.0243),
    "Amritsar": (31.6340, 74.8723),
    "Faridabad": (28.4089, 77.3178),
    "Allahabad": (25.4358, 81.8463),
    "Prayagraj": (25.4358, 81.8463),
    "Mathura": (27.4924, 77.6737),
    "Bareilly": (28.3670, 79.4304),
    "Aligarh": (27.8974, 78.0880),
    "Moradabad": (28.8386, 78.7733),
    "Saharanpur": (29.9680, 77.5460),
    "Gorakhpur": (26.7606, 83.3732),
    "Firozabad": (27.1591, 78.3957),
    "Jhansi": (25.4484, 78.5685),
    "Ghaziabad": (28.6692, 77.4538),
    "Ludhiana": (30.9010, 75.8573),
    "Jalandhar": (31.3260, 75.5762),
    "Dehradun": (30.3165, 78.0322),
    "Haridwar": (29.9457, 78.1642),
    "Rishikesh": (30.0869, 78.2676),
    "Shimla": (31.1048, 77.1734),
    "Bathinda": (30.2110, 74.9455),
    "Unknown": (20.5937, 78.9629)
}

@router.get("/markers")
def get_map_markers(db: Session = Depends(get_db)):
    """
    Returns markers representing cases last-seen and public sightings.
    """
    cases = case_repo.list_cases(db)
    submissions = sub_repo.list_submissions(db)
    
    markers = []
    
    # Process cases
    for case in cases:
        lat, lon = None, None
        if case.city and case.city in CITY_COORDS:
            lat, lon = CITY_COORDS[case.city]
        else:
            # Check case-insensitive
            for key, val in CITY_COORDS.items():
                if case.city and key.lower() == case.city.lower():
                    lat, lon = val
                    break
        if lat is None:
            lat, lon = CITY_COORDS["Unknown"]
            
        markers.append({
            "type": "case",
            "id": case.id,
            "name": case.name,
            "status": case.status,
            "location_name": f"{case.address}, {case.city}",
            "lat": lat,
            "lon": lon,
            "info": f"Missing: {case.name} | Age: {case.age} | City: {case.city}"
        })
        
    # Process submissions
    for sub in submissions:
        lat = sub.latitude
        lon = sub.longitude
        
        # Use location parsing fallback if coordinates are null
        if lat is None or lon is None:
            if sub.location and sub.location in CITY_COORDS:
                lat, lon = CITY_COORDS[sub.location]
            else:
                for key, val in CITY_COORDS.items():
                    if sub.location and key.lower() == sub.location.lower():
                        lat, lon = val
                        break
        if lat is None or lon is None:
            continue  # Skip sightings without any geo indicators
            
        markers.append({
            "type": "sighting",
            "id": sub.id,
            "name": "Anonymous Sighting" if sub.is_anonymous else sub.submitted_by,
            "status": sub.status,
            "location_name": sub.location,
            "lat": lat,
            "lon": lon,
            "info": f"Sighting: {sub.location} on {sub.submitted_on.strftime('%Y-%m-%d')}"
        })
        
    return markers
