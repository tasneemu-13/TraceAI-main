import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import db_session
from app.models.doc import SightingMatch
from app.models.submission import PublicSubmissions
from app.models.case import RegisteredCases

db = db_session()
try:
    print("Clearing SightingMatch table...")
    db.query(SightingMatch).delete()
    
    print("Clearing PublicSubmissions table...")
    db.query(PublicSubmissions).delete()
    
    print("Clearing RegisteredCases table...")
    db.query(RegisteredCases).delete()
    
    db.commit()
    print("All tables cleared successfully!")
except Exception as e:
    db.rollback()
    print(f"Error clearing tables: {e}")
finally:
    db_session.remove()
