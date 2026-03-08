"""FastAPI main application — Prompt Mirror Backend"""

import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth import (
    create_jwt,
    decode_jwt,
    github_authorize_url,
    github_callback,
    google_authorize_url,
    google_callback,
)
from backend.database import Base, engine, get_db
from backend.models import Prompt, User
from backend.schemas import (
    PromptBatchCreate,
    PromptCreate,
    PromptListOut,
    PromptOut,
    StatsOut,
    TokenResponse,
    UserOut,
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Prompt Mirror API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
allowed_origins = [
    FRONTEND_URL,
    "chrome-extension://*",        # Chrome extension
]
# In production, be specific; during dev, allow localhost variants
if os.getenv("RENDER") is None:
    allowed_origins += ["http://localhost:8501", "http://localhost:3000", "http://127.0.0.1:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security ---
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ==================== Health ====================
@app.get("/health")
def health():
    return {"status": "ok"}


# ==================== Auth: GitHub ====================
@app.get("/auth/github")
def auth_github():
    state = secrets.token_urlsafe(32)
    return RedirectResponse(github_authorize_url(state))


@app.get("/auth/github/callback")
async def auth_github_cb(code: str, state: str | None = None, db: Session = Depends(get_db)):
    user = await github_callback(code, db)
    token = create_jwt(user.id)
    # Redirect to frontend with token in fragment (never in query for security)
    return RedirectResponse(f"{FRONTEND_URL}?token={token}&provider=github")


# ==================== Auth: Google ====================
@app.get("/auth/google")
def auth_google():
    state = secrets.token_urlsafe(32)
    return RedirectResponse(google_authorize_url(state))


@app.get("/auth/google/callback")
async def auth_google_cb(code: str, state: str | None = None, db: Session = Depends(get_db)):
    user = await google_callback(code, db)
    token = create_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}?token={token}&provider=google")


# ==================== Auth: Exchange (for Chrome extension) ====================
@app.get("/auth/me", response_model=UserOut)
def auth_me(user: User = Depends(get_current_user)):
    return user


# ==================== Prompts: CRUD ====================
@app.post("/api/prompts", response_model=PromptOut, status_code=201)
def create_prompt(
    body: PromptCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = Prompt(
        user_id=user.id,
        text=body.text,
        source=body.source,
        client_ts=datetime.utcfromtimestamp(body.client_ts / 1000) if body.client_ts else None,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@app.post("/api/prompts/batch", response_model=dict, status_code=201)
def create_prompts_batch(
    body: PromptBatchCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Batch upload up to 5000 prompts at once (for Chrome extension sync)."""
    objects = []
    for p in body.prompts:
        objects.append(
            Prompt(
                user_id=user.id,
                text=p.text,
                source=p.source,
                client_ts=datetime.utcfromtimestamp(p.client_ts / 1000) if p.client_ts else None,
            )
        )
    db.bulk_save_objects(objects)
    db.commit()
    return {"inserted": len(objects)}


@app.get("/api/prompts", response_model=PromptListOut)
def list_prompts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=50000),
):
    total = db.query(func.count(Prompt.id)).filter(Prompt.user_id == user.id).scalar()
    rows = (
        db.query(Prompt)
        .filter(Prompt.user_id == user.id)
        .order_by(Prompt.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return PromptListOut(
        total=total,
        prompts=[
            PromptOut(
                id=r.id,
                text=r.text,
                source=r.source,
                client_ts=r.client_ts.timestamp() * 1000 if r.client_ts else None,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )


@app.delete("/api/prompts/{prompt_id}", status_code=204)
def delete_prompt(
    prompt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.user_id == user.id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete(prompt)
    db.commit()


@app.delete("/api/prompts", status_code=204)
def delete_all_prompts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Prompt).filter(Prompt.user_id == user.id).delete()
    db.commit()


# ==================== Stats ====================
@app.get("/api/stats", response_model=StatsOut)
def get_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(Prompt.id)).filter(Prompt.user_id == user.id).scalar()
    earliest = db.query(func.min(Prompt.created_at)).filter(Prompt.user_id == user.id).scalar()
    latest = db.query(func.max(Prompt.created_at)).filter(Prompt.user_id == user.id).scalar()
    return StatsOut(total_prompts=total or 0, earliest=earliest, latest=latest)
