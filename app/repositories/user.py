from sqlalchemy.orm import Session
from app.models.user import User

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, db_user: User, update_data: dict) -> User:
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def list_users(db: Session, role: str = None):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()
