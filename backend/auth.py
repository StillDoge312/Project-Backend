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
        
        # Проверяем существующего пользователя
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Пользователь с таким именем уже существует"
        
        # Создаем пользователя с password_hash
        user = User(
            username=username,
            password_hash=pwd_context.hash(password)  # Теперь это поле существует!
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return True, user.id
    except Exception as e:
        db.rollback()
        return False, f"Ошибка базы данных: {str(e)}"
    finally:
        db.close()

def verify_user(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "Пользователь не найден"
        
        if pwd_context.verify(password, user.password_hash):
            return True, user.id
        return False, "Неверный пароль"
    except Exception as e:
        return False, f"Ошибка базы данных: {str(e)}"
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)