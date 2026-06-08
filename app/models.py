"""ORM-модели: пользователь и задача."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=True)           # заполняется ИИ
    estimated_minutes = Column(Integer, nullable=True) # заполняется ИИ
    complexity = Column(String, default="normal")      # normal | high
    is_done = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="tasks")
    parent = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )
    subtasks = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
