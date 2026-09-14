import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "dummy-secret-if-none")

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

def create_jwt(email: str) -> str:
    payload = {
        "sub": email,
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")

@router.post("/signup", response_model=AuthResponse)
async def signup(req: AuthRequest):
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    # Mock signup - in a real app, save to DB
    token = create_jwt(req.email)
    return {"access_token": token, "user_id": req.email}

@router.post("/login", response_model=AuthResponse)
async def login(req: AuthRequest):
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    # Mock login
    token = create_jwt(req.email)
    return {"access_token": token, "user_id": req.email}

@router.post("/google", response_model=AuthResponse)
async def google_login():
    # Mock Google login
    token = create_jwt("google-user@example.com")
    return {"access_token": token, "user_id": "google-user@example.com"}
