from datetime import datetime
from typing import Optional, Tuple, Union

from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal
from .models import User
from .security import build_totp_uri, generate_totp_secret, verify_totp

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip()


def create_user(username: str, password: str, email: Optional[str] = None) -> Tuple[bool, Union[str, dict]]:
    db = SessionLocal()
    try:
        username = _normalize(username)
        email = _normalize(email)
        password = password or ""

        if len(username) < 5:
            return False, "Имя пользователя должно быть не короче 5 символов"
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "Пользователь с таким именем уже существует"

        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return False, "Этот e-mail уже привязан к другому пользователю"

        user = User(
            username=username,
            password_hash=pwd_context.hash(password),
            email=email or None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return True, {"user_id": user.id}
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()


def verify_user(username: str, password: str, otp_code: Optional[str] = None) -> Tuple[bool, Union[str, dict]]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == _normalize(username)).first()
        if not user:
            return False, "Пользователь не найден"

        if not pwd_context.verify(password or "", user.password_hash):
            return False, "Неверный пароль"

        if user.is_2fa_enabled:
            if not otp_code:
                return False, {"code": "2fa_required", "user_id": user.id}
            if not verify_totp(user.otp_secret, otp_code):
                return False, "Неверный одноразовый код"

        user.last_login_at = datetime.utcnow()
        db.commit()
        return True, {"user_id": user.id}
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()


def set_master_key(user_id: int, master_key: str) -> Tuple[bool, str]:
    if len(master_key or "") < 8:
        return False, "Мастер-ключ должен быть не короче 8 символов"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден"

        user.master_key = pwd_context.hash(master_key)
        db.commit()
        return True, "Мастер-ключ сохранён"
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()


def verify_master_key(user_id: int, master_key: str) -> bool:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.master_key:
            return False
        return pwd_context.verify(master_key, user.master_key)
    finally:
        db.close()


def initiate_two_factor_setup(user_id: int) -> Tuple[bool, Union[str, dict]]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден"

        secret = generate_totp_secret()
        user.otp_secret = secret
        user.is_2fa_enabled = False
        db.commit()
        uri = build_totp_uri(secret, user.username)
        return True, {"secret": secret, "otpauth_uri": uri}
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()


def confirm_two_factor(user_id: int, otp_code: str) -> Tuple[bool, str]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.otp_secret:
            return False, "2FA ещё не инициализирована"

        if not verify_totp(user.otp_secret, otp_code):
            return False, "Неверный одноразовый код"

        user.is_2fa_enabled = True
        db.commit()
        return True, "Двухфакторная аутентификация включена"
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()


def disable_two_factor(user_id: int) -> Tuple[bool, str]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден"

        user.is_2fa_enabled = False
        user.otp_secret = None
        db.commit()
        return True, "2FA отключена"
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Ошибка базы данных: {str(exc)}"
    finally:
        db.close()
