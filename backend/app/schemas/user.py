from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = "Viewer"


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: Optional[str] = None
    status: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
