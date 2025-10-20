from fastapi import APIRouter, HTTPException, status
from typing import Optional

from pydantic import BaseModel, EmailStr

from . import credentials as credential_service
from .auth import (
    confirm_two_factor,
    create_user,
    disable_two_factor,
    initiate_two_factor_setup,
    verify_user,
)

router = APIRouter(prefix="/api", tags=["api"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: Optional[str] = None


class CredentialCreateRequest(BaseModel):
    user_id: int
    title: str
    password: str
    login: Optional[str] = None
    notes: Optional[str] = None


class CredentialUpdateRequest(BaseModel):
    user_id: int
    credential_id: int
    title: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None


@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register(payload: RegisterRequest):
    ok, res = create_user(payload.username, payload.password, payload.email)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
    return {"message": "user created", **res}


@router.post("/login")
def api_login(payload: LoginRequest):
    ok, res = verify_user(payload.username, payload.password, payload.otp_code)
    if ok:
        return {"message": "login successful", **res}

    if isinstance(res, dict) and res.get("code") == "2fa_required":
        return {"message": "two_factor_required", **res}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=res)


@router.post("/2fa/setup")
def api_2fa_setup(user_id: int):
    ok, res = initiate_two_factor_setup(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
    return res


@router.post("/2fa/confirm")
def api_2fa_confirm(user_id: int, code: str):
    ok, message = confirm_two_factor(user_id, code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


@router.post("/2fa/disable")
def api_2fa_disable(user_id: int):
    ok, message = disable_two_factor(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


@router.get("/credentials/{user_id}")
def api_list_credentials(user_id: int, include_sensitive: bool = False):
    return credential_service.list_credentials(user_id, include_sensitive=include_sensitive)


@router.post("/credentials")
def api_create_credential(payload: CredentialCreateRequest):
    ok, res = credential_service.create_credential(
        payload.user_id,
        payload.title,
        payload.password,
        login=payload.login,
        notes=payload.notes,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
    return res


@router.put("/credentials")
def api_update_credential(payload: CredentialUpdateRequest):
    ok, res = credential_service.update_credential(
        payload.user_id,
        payload.credential_id,
        title=payload.title,
        login=payload.login,
        password=payload.password,
        notes=payload.notes,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
    return res


@router.delete("/credentials/{user_id}/{credential_id}")
def api_delete_credential(user_id: int, credential_id: int):
    ok, message = credential_service.delete_credential(user_id, credential_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}
