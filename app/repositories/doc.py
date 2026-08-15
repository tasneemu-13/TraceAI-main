from sqlalchemy.orm import Session
from app.models.doc import InvestigationDoc

def create_doc(db: Session, doc: InvestigationDoc) -> InvestigationDoc:
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_docs_by_case(db: Session, case_id: str):
    return db.query(InvestigationDoc).filter(InvestigationDoc.case_id == case_id).all()

def delete_doc(db: Session, doc_id: int) -> bool:
    db_doc = db.query(InvestigationDoc).filter(InvestigationDoc.id == doc_id).first()
    if db_doc:
        db.delete(db_doc)
        db.commit()
        return True
    return False

def list_all_docs(db: Session):
    return db.query(InvestigationDoc).all()
