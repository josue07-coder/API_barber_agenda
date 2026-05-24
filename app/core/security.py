from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
    hashed = bcrypt.hashpw(sha.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return bcrypt.checkpw(
        sha.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire_delta = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
