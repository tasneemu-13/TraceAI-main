import os
import random
import string
from datetime import datetime, timedelta
import bcrypt
import jwt
from typing import Optional, Union, Dict
from app.config import settings
from app.services.notification import send_email
from app.database import SessionLocal
from app.models.user import User

# --- Passwords ---
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    if not any(c in string.punctuation for c in password):
        return False, "Password must contain at least one special character."
    return True, "Strong password."

# --- JWT Tokens ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Expired
    except jwt.InvalidTokenError:
        return None  # Invalid

# --- OTP (One-Time Password) ---
def generate_otp() -> str:
    """Generate a random 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=6))

def store_otp(identifier: str, otp: str, expires_in_minutes: int = 5):
    """Store generated OTP inside the database to survive server restarts."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == identifier).first()
        if user:
            # Save in format "otp_code:expiration_timestamp"
            expiry_ts = (datetime.utcnow() + timedelta(minutes=expires_in_minutes)).timestamp()
            user.otp_secret = f"{otp}:{expiry_ts}"
            db.commit()
    except Exception as e:
        print(f"[Store OTP Error] Failed to persist OTP in DB: {e}")
    finally:
        db.close()

def verify_otp(identifier: str, input_otp: str) -> bool:
    """Verify input OTP against database entry, checking expiration."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == identifier).first()
        if not user or not user.otp_secret:
            return False
            
        parts = user.otp_secret.split(":")
        if len(parts) != 2:
            return False
            
        stored_otp, expiry_ts_str = parts
        expiry_ts = float(expiry_ts_str)
        
        # Check expiry
        if datetime.utcnow().timestamp() > expiry_ts:
            user.otp_secret = None
            db.commit()
            return False
            
        if stored_otp == input_otp:
            user.otp_secret = None
            db.commit()
            return True
            
        return False
    except Exception as e:
        print(f"[Verify OTP Error] Failed to verify OTP: {e}")
        return False
    finally:
        db.close()
