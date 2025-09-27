# backend/auth.py
from passlib.context import CryptContext
from .db import SessionLocal
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, password: str):
    db = SessionLocal()
    try:
        if len(username) < 5:
            return False, "Логин должен быть не короче 5 символов"
        if len(password) < 5:
            return False, "Пароль должен быть не короче 5 символов"
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Username already exists"
        user = User(username=username, password_hash=pwd_context.hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return True, user.id
    finally:
        db.close()

def verify_user(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "User not found"
        if pwd_context.verify(password, user.password_hash):
            return True, user.id
        return False, "Invalid password"
    finally:
        db.close()
