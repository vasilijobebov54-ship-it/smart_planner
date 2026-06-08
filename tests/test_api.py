"""
Тесты API. AI-сервис замокан, чтобы тесты не ходили в сеть.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import ai_service
from app.database import Base, get_db
from app.main import app


# Изолированная БД в памяти для тестов
TEST_DB_URL = "sqlite:///./test_planner.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Перед каждым тестом — чистая БД."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    """Не ходим в сеть — подменяем функции AI-сервиса фиксированными значениями."""
    monkeypatch.setattr(ai_service, "categorize_task", lambda d: "работа")
    monkeypatch.setattr(ai_service, "estimate_minutes", lambda d: 25)
    monkeypatch.setattr(
        ai_service, "split_into_subtasks",
        lambda d: ["Шаг 1", "Шаг 2", "Шаг 3"],
    )


client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_user():
    r = client.post("/users", json={"username": "alice"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert "id" in body


def test_create_task_sets_ai_fields():
    user = client.post("/users", json={"username": "bob"}).json()
    r = client.post(
        f"/tasks?owner_id={user['id']}",
        json={
            "title": "Подготовить отчёт",
            "description": "Собрать данные и оформить отчёт за квартал",
        },
    )
    assert r.status_code == 201, r.text
    task = r.json()
    assert task["category"] == "работа"
    assert task["estimated_minutes"] == 25
    assert task["complexity"] == "normal"
    assert task["subtasks"] == []


def test_create_high_complexity_task_spawns_subtasks():
    user = client.post("/users", json={"username": "carol"}).json()
    r = client.post(
        f"/tasks?owner_id={user['id']}",
        json={
            "title": "Запустить проект",
            "description": "Запустить с нуля новый веб-проект",
            "complexity": "high",
        },
    )
    assert r.status_code == 201
    task = r.json()
    assert len(task["subtasks"]) == 3
    titles = [s["title"] for s in task["subtasks"]]
    assert titles == ["Шаг 1", "Шаг 2", "Шаг 3"]


def test_create_task_unknown_owner():
    r = client.post(
        "/tasks?owner_id=999",
        json={"title": "X", "description": "Y"},
    )
    assert r.status_code == 404


def test_list_and_get_task():
    user = client.post("/users", json={"username": "dave"}).json()
    created = client.post(
        f"/tasks?owner_id={user['id']}",
        json={"title": "T", "description": "D"},
    ).json()

    lst = client.get(f"/tasks?owner_id={user['id']}").json()
    assert len(lst) == 1

    one = client.get(f"/tasks/{created['id']}").json()
    assert one["id"] == created["id"]


def test_update_and_delete_task():
    user = client.post("/users", json={"username": "eve"}).json()
    created = client.post(
        f"/tasks?owner_id={user['id']}",
        json={"title": "T", "description": "D"},
    ).json()

    r = client.patch(f"/tasks/{created['id']}", json={"is_done": True})
    assert r.status_code == 200
    assert r.json()["is_done"] is True

    r = client.delete(f"/tasks/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404
