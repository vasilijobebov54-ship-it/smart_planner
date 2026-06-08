"""Pydantic-схемы для входа/выхода API."""
from datetime import datetime
from typing import Optional, List, Literal, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ---------- User ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


# ---------- Task ----------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    complexity: Literal["normal", "high"] = "normal"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_done: Optional[bool] = None
    complexity: Optional[Literal["normal", "high"]] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: Optional[str]
    estimated_minutes: Optional[int]
    complexity: str
    is_done: bool
    parent_id: Optional[int]
    owner_id: int
    created_at: datetime
    subtasks: List["TaskOut"] = Field(default_factory=list)

    @field_validator("subtasks", mode="before")
    @classmethod
    def _none_to_empty(cls, v: Any) -> Any:
        return v if v is not None else []


TaskOut.model_rebuild()
