import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Index, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(20), nullable=False)          # "github" | "google"
    provider_id = Column(String(128), nullable=False)       # ID from OAuth provider
    email = Column(String(256), nullable=True)
    display_name = Column(String(256), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prompts = relationship("Prompt", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_user_provider", "provider", "provider_id", unique=True),
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    source = Column(String(64), nullable=True)              # "chatgpt", "claude", "gemini", etc.
    client_ts = Column(DateTime, nullable=True)              # Timestamp from Chrome extension
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="prompts")

    __table_args__ = (
        Index("ix_prompt_user_created", "user_id", "created_at"),
    )
