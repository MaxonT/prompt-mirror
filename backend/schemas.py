from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# --- Auth ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


# --- Prompts ---
class PromptCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    source: Optional[str] = Field(None, max_length=64)
    client_ts: Optional[float] = None  # epoch ms from Chrome extension


class PromptBatchCreate(BaseModel):
    prompts: list[PromptCreate] = Field(..., max_length=5000)


class PromptOut(BaseModel):
    id: int
    text: str
    source: Optional[str]
    client_ts: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class PromptListOut(BaseModel):
    total: int
    prompts: list[PromptOut]


class UserOut(BaseModel):
    id: str
    provider: str
    email: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_prompts: int
    earliest: Optional[datetime]
    latest: Optional[datetime]
