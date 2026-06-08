"""
FastAPI-приложение: Smart Task Planner.

Эндпоинты:
    POST /users               — создать пользователя
    POST /tasks                — создать задачу (ИИ ставит категорию и оценку времени;
                                 если complexity=high — агент создаёт 3 подзадачи)
    GET  /tasks                — список задач (фильтр по owner_id)
    GET  /tasks/{id}           — одна задача
    PATCH /tasks/{id}          — обновить
    DELETE /tasks/{id}         — удалить
"""
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from . import crud, models, schemas, ai_service
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Task Planner",
    description="Умный планировщик задач с интеграцией ИИ (Anthropic Claude).",
    version="1.0.0",
)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "Smart Task Planner"}


# ---------- Users ----------
@app.post(
    "/users",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, data)


# ---------- Tasks ----------
@app.post(
    "/tasks",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
)
def create_task(
    data: schemas.TaskCreate,
    owner_id: int = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, owner_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # ИИ: категория + оценка времени
    category = ai_service.categorize_task(data.description)
    minutes = ai_service.estimate_minutes(data.description)

    task = crud.create_task(
        db, data, owner_id=owner_id,
        category=category, estimated_minutes=minutes,
    )

    # Агент: для сложных задач — автоматически разбить на 3 подзадачи
    if data.complexity == "high":
        subtitles = ai_service.split_into_subtasks(data.description)
        for sub_title in subtitles:
            sub_data = schemas.TaskCreate(
                title=sub_title[:200],
                description=sub_title,
                complexity="normal",
            )
            sub_cat = ai_service.categorize_task(sub_title)
            sub_min = ai_service.estimate_minutes(sub_title)
            crud.create_task(
                db, sub_data, owner_id=owner_id,
                category=sub_cat, estimated_minutes=sub_min,
                parent_id=task.id,
            )
        db.refresh(task)
        _ = task.subtasks  # принудительно подгружаем relationship для сериализации

    return task


@app.get("/tasks", response_model=List[schemas.TaskOut], tags=["tasks"])
def list_tasks(
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud.list_tasks(db, owner_id=owner_id)


@app.get("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["tasks"])
def update_task(
    task_id: int, data: schemas.TaskUpdate, db: Session = Depends(get_db)
):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return crud.update_task(db, task, data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    crud.delete_task(db, task)
    return None
