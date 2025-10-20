import base64
import hashlib
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
import pyotp

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_DIR = BASE_DIR / "data"
FERNET_KEY_PATH = SECRET_DIR / "fernet.key"
APP_FERNET_ENV = "APP_SECRET_KEY"


def _derive_key_from_env(secret: str) -> bytes:
    """Derive a Fernet-compatible key from the provided secret string."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _load_env_key() -> Optional[bytes]:
    secret = os.getenv(APP_FERNET_ENV)
    if secret:
        return _derive_key_from_env(secret)
    return None


def _load_key_from_file() -> Optional[bytes]:
    if FERNET_KEY_PATH.exists():
        key = FERNET_KEY_PATH.read_bytes().strip()
        if key:
            return key
    return None


def _persist_key_to_file(key: bytes) -> None:
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    FERNET_KEY_PATH.write_bytes(key)


def load_fernet_key() -> bytes:
    """Load or create a persistent Fernet key used for credential encryption."""
    env_key = _load_env_key()
    if env_key:
        return env_key

    file_key = _load_key_from_file()
    if file_key:
        return file_key

    new_key = Fernet.generate_key()
    _persist_key_to_file(new_key)
    return new_key


def get_cipher() -> Fernet:
    return Fernet(load_fernet_key())


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """Encrypt a plain string with Fernet. Returns None for falsy inputs."""
    if not value:
        return value
    cipher = get_cipher()
    return cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: Optional[str]) -> Optional[str]:
    """Decrypt a Fernet token, returning None if invalid or empty."""
    if not token:
        return token
    cipher = get_cipher()
    try:
        return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


# 2FA helpers ---------------------------------------------------------------

DEFAULT_ISSUER = "Key Manager"


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(secret: str, username: str, issuer: str = DEFAULT_ISSUER) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    if not (secret and code):
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
