from datetime import datetime
from typing import List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal
from .models import Credential
from .security import decrypt_value, encrypt_value


def _serialize(credential: Credential, include_sensitive: bool = False) -> dict:
    data = {
        "id": credential.id,
        "title": credential.title,
        "login": credential.login,
        "created_at": credential.created_at,
        "updated_at": credential.updated_at,
        "is_archived": credential.is_archived,
    }
    if include_sensitive:
        data["password"] = decrypt_value(credential.password_encrypted)
        data["notes"] = decrypt_value(credential.notes_encrypted)
    return data


def list_credentials(user_id: int, include_sensitive: bool = False) -> List[dict]:
    db = SessionLocal()
    try:
        records = (
            db.query(Credential)
            .filter(Credential.user_id == user_id, Credential.is_archived.is_(False))
            .order_by(Credential.created_at.desc())
            .all()
        )
        return [_serialize(record, include_sensitive=include_sensitive) for record in records]
    finally:
        db.close()


def get_credential(user_id: int, credential_id: int, include_sensitive: bool = False) -> Optional[dict]:
    db = SessionLocal()
    try:
        credential = (
            db.query(Credential)
            .filter(Credential.user_id == user_id, Credential.id == credential_id)
            .first()
        )
        if not credential:
            return None
        return _serialize(credential, include_sensitive=include_sensitive)
    finally:
        db.close()


def create_credential(
    user_id: int,
    title: str,
    password: str,
    login: Optional[str] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, Union[str, dict]]:
    db = SessionLocal()
    try:
        clean_title = (title or "").strip()
        if not clean_title:
            return False, "Title is required"
        if not password:
            return False, "Password cannot be empty"

        exists = (
            db.query(Credential)
            .filter(Credential.user_id == user_id, Credential.title == clean_title)
            .first()
        )
        if exists:
            return False, "Credential with this title already exists"

        credential = Credential(
            user_id=user_id,
            title=clean_title,
            login=(login or "").strip() or None,
            password_encrypted=encrypt_value(password),
            notes_encrypted=encrypt_value(notes or ""),
            created_at=datetime.utcnow(),
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
        return True, _serialize(credential, include_sensitive=True)
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Database error: {exc}"
    finally:
        db.close()


def update_credential(
    user_id: int,
    credential_id: int,
    *,
    title: Optional[str] = None,
    login: Optional[str] = None,
    password: Optional[str] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, Union[str, dict]]:
    db = SessionLocal()
    try:
        credential = (
            db.query(Credential)
            .filter(Credential.user_id == user_id, Credential.id == credential_id)
            .first()
        )
        if not credential:
            return False, "Credential not found"

        if title is not None:
            new_title = title.strip()
            if not new_title:
                return False, "Title cannot be empty"
            duplicate = (
                db.query(Credential)
                .filter(
                    Credential.user_id == user_id,
                    Credential.title == new_title,
                    Credential.id != credential_id,
                )
                .first()
            )
            if duplicate:
                return False, "Another credential with this title already exists"
            credential.title = new_title

        if login is not None:
            credential.login = login.strip() or None

        if password is not None and password != "":
            credential.password_encrypted = encrypt_value(password)

        if notes is not None:
            credential.notes_encrypted = encrypt_value(notes)

        credential.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(credential)
        return True, _serialize(credential, include_sensitive=True)
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Database error: {exc}"
    finally:
        db.close()


def delete_credential(user_id: int, credential_id: int) -> Tuple[bool, str]:
    db = SessionLocal()
    try:
        credential = (
            db.query(Credential)
            .filter(Credential.user_id == user_id, Credential.id == credential_id)
            .first()
        )
        if not credential:
            return False, "Credential not found"

        db.delete(credential)
        db.commit()
        return True, "Credential removed"
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Database error: {exc}"
    finally:
        db.close()
