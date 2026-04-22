import os
import time
import json
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from jose import jwt
from db_utils import get_or_create_google_client

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter(prefix="/auth/google", tags=["auth-google"])


def create_app_jwt(google_user: dict, client_id: int) -> str:
    """Создаём JWT для нашего приложения на основе данных Google."""
    payload = {
        "sub": google_user.get("sub") or google_user.get("id"),
        "email": google_user.get("email"),
        "name": google_user.get("name"),
        "picture": google_user.get("picture"),
        "client_id": client_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60 * 24,  # 24 часа
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.get("/login")
def google_login():
    """
    Возвращает URL авторизации Google, на который надо отправить пользователя.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"auth_url": auth_url}


@router.get("/callback")
def google_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    Принимает редирект от Google с code, обменивает на токен и возвращает JWT.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google auth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter")

    # Обмен code на access_token / id_token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_resp = requests.post(token_url, data=data, timeout=15)
    if not token_resp.ok:
        raise HTTPException(status_code=400, detail=f"Failed to get tokens from Google: {token_resp.text}")

    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    if not id_token:
        raise HTTPException(status_code=400, detail="No id_token returned by Google")

    # Получить профиль пользователя через /userinfo (можно также декодировать id_token)
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token returned by Google")

    userinfo_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if not userinfo_resp.ok:
        raise HTTPException(status_code=400, detail=f"Failed to get userinfo: {userinfo_resp.text}")

    google_user = userinfo_resp.json()
    email = google_user.get("email")
    name = google_user.get("name") or "google_user"
    if not email:
        raise HTTPException(status_code=400, detail="Google account email is missing")

    client_id = get_or_create_google_client(email=email, name=name)
    if not client_id:
        raise HTTPException(status_code=500, detail="Failed to map Google user to local account")

    app_jwt = create_app_jwt(google_user, client_id)

    # Вариант 1: редиректим во фронтенд с токеном в query (или hash)
    redirect_url = f"{FRONTEND_ORIGIN}/auth/callback?token={app_jwt}"
    return RedirectResponse(url=redirect_url, status_code=302)