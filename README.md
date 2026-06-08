# Smart Task Planner

Умный планировщик задач на **FastAPI + SQLite** с интеграцией **Anthropic Claude** для автокатегоризации, оценки времени и автоматического разбиения сложных задач на подзадачи (AI-агент).

## Возможности

- CRUD по задачам и пользователям.
- При создании задачи ИИ автоматически:
  - проставляет **категорию** (`работа` / `личное` / `здоровье` / `обучение` / `другое`);
  - оценивает **время выполнения в минутах**.
- Если задача отмечена как `complexity=high`, **AI-агент** разбивает её на 3 подзадачи и создаёт их в БД.
- Если ключа API нет — приложение работает с безопасными дефолтами (категория `другое`, 30 минут), ничего не падает.
- Авто-документация Swagger по адресу `/docs`, ReDoc — `/redoc`, OpenAPI JSON — `/openapi.json`.

## Структура

```
smart_planner/
├── app/
│   ├── main.py          # FastAPI и роуты
│   ├── models.py        # SQLAlchemy ORM
│   ├── schemas.py       # Pydantic схемы
│   ├── database.py      # подключение к SQLite
│   ├── crud.py          # CRUD-функции
│   └── ai_service.py    # вызов Claude API + парсеры
├── tests/
│   ├── test_ai_parsing.py
│   └── test_api.py
├── requirements.txt
├── .env.example
└── README.md
```

## Установка и запуск

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # пропиши свой ANTHROPIC_API_KEY
export $(cat .env | xargs)        # или используй python-dotenv

uvicorn app.main:app --reload
```

Открой <http://127.0.0.1:8000/docs> — там Swagger UI с возможностью потыкать API руками.

## Запуск тестов

```bash
pytest -v
```

В тестах AI-сервис замокан, сеть не дёргается.

## API кратко

| Метод  | URL                  | Описание                                 |
|--------|----------------------|------------------------------------------|
| POST   | `/users`             | Создать пользователя                     |
| POST   | `/tasks?owner_id=N`  | Создать задачу (ИИ заполнит cat + мин)   |
| GET    | `/tasks?owner_id=N`  | Список задач                             |
| GET    | `/tasks/{id}`        | Одна задача                              |
| PATCH  | `/tasks/{id}`        | Обновить                                 |
| DELETE | `/tasks/{id}`        | Удалить                                  |

### Пример

```bash
curl -X POST "http://127.0.0.1:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}'

curl -X POST "http://127.0.0.1:8000/tasks?owner_id=1" \
  -H "Content-Type: application/json" \
  -d '{
        "title": "Подготовить презентацию",
        "description": "Сделать слайды по итогам спринта",
        "complexity": "high"
      }'
```

В ответ придёт задача с заполненными `category`, `estimated_minutes` и тремя `subtasks`.

## Переключение на локальную модель (Ollama)

`app/ai_service.py` инкапсулирует всю работу с моделью внутри `_call_claude`.
Чтобы переехать на Ollama, замените тело этой функции на запрос к
`http://localhost:11434/api/generate` и формат ответа Ollama. Парсеры
(`parse_category`, `parse_minutes`, `parse_subtasks`) и высокоуровневые функции
остаются без изменений — это сознательное архитектурное решение.

## AI Assistant Log

См. файл [`AI_ASSISTANT_LOG.md`](./AI_ASSISTANT_LOG.md) — там история ключевых
промптов к ИИ и решений, принятых по результатам.
