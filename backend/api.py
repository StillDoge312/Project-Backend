# backend/api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .auth import create_user, verify_user

router = APIRouter(prefix="/api", tags=["api"])

class AuthRequest(BaseModel):
    username: str
    password: str

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.post("/register")
def api_register(data: AuthRequest):
    ok, res = create_user(data.username, data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"message": "user created", "user_id": res}

@router.post("/login")
def api_login(data: AuthRequest):
    ok, res = verify_user(data.username, data.password)
    if not ok:
        raise HTTPException(status_code=401, detail=res)
    return {"message": "login successful", "user_id": res}
