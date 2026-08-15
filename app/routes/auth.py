from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.repositories import user as user_repo
from app.models.user import User
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    city: str
    area: str

class LoginRequest(BaseModel):
    username: str
    password: str

class OTPVerifyRequest(BaseModel):
    identifier: str  # username or email
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username or email exists
    if user_repo.get_user_by_username(db, req.username):
        raise HTTPException(status_code=400, detail="Username already registered.")
    if user_repo.get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    # Check password strength
    ok, msg = auth_service.validate_password_strength(req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    # Create new user
    new_user = User(
        username=req.username,
        email=req.email,
        hashed_password=auth_service.hash_password(req.password),
        role="Public",
        name=req.name,
        city=req.city,
        area=req.area,
        is_verified=False
    )
    user_repo.create_user(db, new_user)
    return {"message": "Registration successful. Please verify your email."}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    db_user = user_repo.get_user_by_username(db, req.username)
    if not db_user or not auth_service.verify_password(req.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password.")
        
    # Check MFA / OTP (simulating OTP trigger)
    otp = auth_service.generate_otp()
    auth_service.store_otp(db_user.email, otp)
    auth_service.send_email(
        db_user.email,
        "TraceAI - Login Verification OTP",
        f"Your verification code is: {otp}. This code is valid for 5 minutes."
    )
    
    return {
        "message": "OTP sent to your registered email.",
        "email": db_user.email,
        "requires_otp": True
    }

@router.post("/verify-otp")
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    # Try identifying by email or username
    db_user = user_repo.get_user_by_username(db, req.identifier)
    if not db_user:
        db_user = user_repo.get_user_by_email(db, req.identifier)
        
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if not auth_service.verify_otp(db_user.email, req.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    # Mark user verified if first login
    if not db_user.is_verified:
        user_repo.update_user(db, db_user, {"is_verified": True})
        
    # Generate JWT tokens
    user_data = {"sub": db_user.username, "role": db_user.role}
    access_token = auth_service.create_access_token(user_data)
    refresh_token = auth_service.create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username,
            "role": db_user.role,
            "name": db_user.name
        }
    }

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = user_repo.get_user_by_email(db, req.email)
    if not db_user:
        # Avoid user enumeration attacks, return success even if email is missing
        return {"message": "If the email exists, an OTP has been sent."}
        
    otp = auth_service.generate_otp()
    auth_service.store_otp(db_user.email, otp)
    auth_service.send_email(
        db_user.email,
        "TraceAI - Password Reset OTP",
        f"Your password reset verification code is: {otp}. This code is valid for 5 minutes."
    )
    return {"message": "If the email exists, an OTP has been sent."}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    db_user = user_repo.get_user_by_email(db, req.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if not auth_service.verify_otp(db_user.email, req.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    # Validate new password strength
    ok, msg = auth_service.validate_password_strength(req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    # Update password
    user_repo.update_user(db, db_user, {"hashed_password": auth_service.hash_password(req.new_password)})
    return {"message": "Password reset successful. You can now login with your new password."}
