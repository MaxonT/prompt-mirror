"""OAuth authentication module — GitHub + Google OAuth 2.0"""

import os
import secrets
from datetime import datetime, timedelta

import httpx
import jwt
from sqlalchemy.orm import Session

from backend.models import User

# --- Config ---
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(64))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# --- JWT helpers ---
def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# --- User upsert ---
def upsert_user(
    db: Session,
    *,
    provider: str,
    provider_id: str,
    email: str | None,
    display_name: str | None,
    avatar_url: str | None,
) -> User:
    user = (
        db.query(User)
        .filter(User.provider == provider, User.provider_id == provider_id)
        .first()
    )
    if user:
        user.email = email or user.email
        user.display_name = display_name or user.display_name
        user.avatar_url = avatar_url or user.avatar_url
        user.last_login = datetime.utcnow()
    else:
        user = User(
            provider=provider,
            provider_id=str(provider_id),
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- GitHub OAuth ---
def github_authorize_url(state: str) -> str:
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={API_BASE_URL}/auth/github/callback"
        f"&scope=read:user user:email"
        f"&state={state}"
    )


async def github_callback(code: str, db: Session) -> User:
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # Fetch user profile
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        profile = user_resp.json()

        # Fetch primary email
        email = profile.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if emails_resp.status_code == 200:
                for e in emails_resp.json():
                    if e.get("primary"):
                        email = e["email"]
                        break

    return upsert_user(
        db,
        provider="github",
        provider_id=str(profile["id"]),
        email=email,
        display_name=profile.get("login") or profile.get("name"),
        avatar_url=profile.get("avatar_url"),
    )


# --- Google OAuth ---
def google_authorize_url(state: str) -> str:
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={API_BASE_URL}/auth/google/callback"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
        f"&state={state}"
    )


async def google_callback(code: str, db: Session) -> User:
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{API_BASE_URL}/auth/google/callback",
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        # Fetch user info
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_resp.raise_for_status()
        profile = user_resp.json()

    return upsert_user(
        db,
        provider="google",
        provider_id=str(profile["id"]),
        email=profile.get("email"),
        display_name=profile.get("name"),
        avatar_url=profile.get("picture"),
    )
