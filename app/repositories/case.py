from sqlalchemy.orm import Session
from app.models.case import RegisteredCases

def get_case_by_id(db: Session, case_id: str) -> RegisteredCases:
    return db.query(RegisteredCases).filter(RegisteredCases.id == case_id).first()

def create_case(db: Session, case: RegisteredCases) -> RegisteredCases:
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

def update_case(db: Session, case_id: str, fields: dict) -> RegisteredCases:
    db_case = get_case_by_id(db, case_id)
    if db_case:
        for key, value in fields.items():
            setattr(db_case, key, value)
        db.commit()
        db.refresh(db_case)
    return db_case

def list_cases(db: Session, status: str = None, submitted_by: str = None):
    query = db.query(RegisteredCases)
    if status and status != "All":
        query = query.filter(RegisteredCases.status == status)
    if submitted_by:
        query = query.filter(RegisteredCases.submitted_by == submitted_by)
    return query.all()

def get_cases_count_by_city(db: Session):
    result = db.query(RegisteredCases.city, RegisteredCases.status).all()
    counts = {}
    for city, status in result:
        city_name = city or "Unknown"
        if city_name not in counts:
            counts[city_name] = {"found": 0, "not_found": 0}
        if status == "F":
            counts[city_name]["found"] += 1
        else:
            counts[city_name]["not_found"] += 1
    return counts

def delete_case(db: Session, case_id: str) -> bool:
    db_case = get_case_by_id(db, case_id)
    if db_case:
        db.delete(db_case)
        db.commit()
        return True
    return False
