"""
AI-сервис.

Общается с Anthropic Claude API. Делает три вещи:
1) Категоризирует задачу.
2) Оценивает время выполнения в минутах.
3) Разбивает сложную задачу на 3 подзадачи (агент).

Если ключа API нет или вызов упал — функции возвращают безопасные значения
по умолчанию, чтобы приложение не падало.
"""
from __future__ import annotations

import os
import logging
import re
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

VALID_CATEGORIES = {"работа", "личное", "здоровье", "обучение", "другое"}


def _call_claude(prompt: str, max_tokens: int = 200) -> Optional[str]:
    """Низкоуровневый вызов API. Возвращает текст ответа или None при ошибке."""
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY не задан — пропускаю вызов AI")
        return None

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            # Ответ: {"content": [{"type": "text", "text": "..."}], ...}
            blocks = data.get("content", [])
            for b in blocks:
                if b.get("type") == "text":
                    return b.get("text", "").strip()
            return None
    except httpx.HTTPError as e:
        logger.error("Ошибка вызова Claude API: %s", e)
        return None
    except Exception as e:  # noqa: BLE001 — последняя линия защиты
        logger.exception("Неожиданная ошибка AI-вызова: %s", e)
        return None


# ---------- Парсеры (вынесены отдельно — их проще тестировать) ----------

def parse_category(raw: Optional[str]) -> str:
    """Достаёт корректную категорию из ответа модели. Default: 'другое'."""
    if not raw:
        return "другое"
    text = raw.strip().lower()
    # модель могла вернуть кавычки, точки и т.п.
    text = re.sub(r"[^а-яa-z]", " ", text)
    for word in text.split():
        if word in VALID_CATEGORIES:
            return word
    return "другое"


def parse_minutes(raw: Optional[str]) -> int:
    """Достаёт целое число минут из ответа модели. Default: 30."""
    if not raw:
        return 30
    m = re.search(r"\d+", raw)
    if not m:
        return 30
    value = int(m.group(0))
    # ограничим разумным диапазоном
    return max(1, min(value, 60 * 24))


def parse_subtasks(raw: Optional[str]) -> List[str]:
    """
    Достаёт список подзадач. Ожидаем формат '1. ...\\n2. ...\\n3. ...'.
    Если не получилось — возвращаем пустой список.
    """
    if not raw:
        return []
    lines = [ln.strip(" -•\t") for ln in raw.splitlines() if ln.strip()]
    # убираем нумерацию '1.' / '1)' в начале
    cleaned = [re.sub(r"^\d+[.)]\s*", "", ln) for ln in lines]
    cleaned = [ln for ln in cleaned if ln]
    return cleaned[:3]


# ---------- Высокоуровневые функции ----------

def categorize_task(description: str) -> str:
    prompt = (
        "Отнеси эту задачу к одной из категорий: работа, личное, здоровье, "
        "обучение, другое. Верни ТОЛЬКО название категории одним словом.\n\n"
        f"Задача: {description}"
    )
    return parse_category(_call_claude(prompt, max_tokens=20))


def estimate_minutes(description: str) -> int:
    prompt = (
        "Оцени, сколько минут займёт выполнение этой задачи. "
        "Это ежедневная задача в личном планировщике. "
        "Верни ТОЛЬКО число.\n\n"
        f"Задача: {description}"
    )
    return parse_minutes(_call_claude(prompt, max_tokens=20))


def split_into_subtasks(description: str) -> List[str]:
    """Цепочка промптов: сложная задача -> 3 конкретных подзадачи."""
    prompt = (
        "Разбей сложную задачу на ровно 3 конкретных подзадачи. "
        "Каждая подзадача — короткая фраза действия. "
        "Формат ответа строго такой:\n"
        "1. ...\n2. ...\n3. ...\n\n"
        f"Сложная задача: {description}"
    )
    subs = parse_subtasks(_call_claude(prompt, max_tokens=300))
    if len(subs) < 3:
        # запасной вариант, если модель ответила криво
        subs = (subs + [
            "Спланировать выполнение",
            "Выполнить основную работу",
            "Проверить результат",
        ])[:3]
    return subs
