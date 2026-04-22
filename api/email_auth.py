import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel

from db_utils import get_or_create_google_client, get_client_by_id


JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def create_app_jwt(user: dict, client_id: int) -> str:
    """JWT для нашего приложения — кладём client_id и основные поля пользователя."""
    payload = {
        "sub": user.get("sub") or str(client_id),
        "email": user.get("email"),
        "name": user.get("name"),
        "client_id": client_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60 * 24,  # 24 часа
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


router = APIRouter(prefix="/auth/email", tags=["auth-email"])


class EmailLoginRequest(BaseModel):
    email: str
    name: Optional[str] = None


@router.post("/login")
def email_login(payload: EmailLoginRequest):
    """
    Простой вход/регистрация по email без пароля.
    Если пользователь с таким email есть — выдаёт ему JWT,
    если нет — создаёт запись в clients и выдаёт JWT.
    """
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    name = (payload.name or "").strip() or email.split("@")[0]

    client_id = get_or_create_google_client(email=email, name=name)
    if not client_id:
        raise HTTPException(status_code=500, detail="Failed to create/find user")

    client = get_client_by_id(client_id) or {}
    user_like = {
        "sub": str(client_id),
        "email": client.get("email", email),
        "name": client.get("username", name),
    }

    token = create_app_jwt(user_like, client_id)
    return {
        "token": token,
        "user": {
            "id": client_id,
            "email": user_like["email"],
            "name": user_like["name"],
        },
    }
