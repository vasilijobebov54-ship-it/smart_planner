"""CRUD-операции с БД."""
from typing import List, Optional
from sqlalchemy.orm import Session

from . import models, schemas


# ---------- Users ----------
def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    user = models.User(username=data.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


# ---------- Tasks ----------
def create_task(
    db: Session,
    data: schemas.TaskCreate,
    owner_id: int,
    category: Optional[str] = None,
    estimated_minutes: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> models.Task:
    task = models.Task(
        title=data.title,
        description=data.description,
        complexity=data.complexity,
        category=category,
        estimated_minutes=estimated_minutes,
        owner_id=owner_id,
        parent_id=parent_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def list_tasks(db: Session, owner_id: Optional[int] = None) -> List[models.Task]:
    q = db.query(models.Task).filter(models.Task.parent_id.is_(None))
    if owner_id is not None:
        q = q.filter(models.Task.owner_id == owner_id)
    return q.order_by(models.Task.created_at.desc()).all()


def update_task(
    db: Session, task: models.Task, data: schemas.TaskUpdate
) -> models.Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
