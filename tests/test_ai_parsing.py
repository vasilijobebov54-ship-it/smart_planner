"""Тесты парсеров ответов ИИ."""
from app.ai_service import parse_category, parse_minutes, parse_subtasks


# ---------- parse_category ----------
def test_parse_category_clean():
    assert parse_category("работа") == "работа"


def test_parse_category_with_noise():
    assert parse_category(' "Здоровье".') == "здоровье"


def test_parse_category_unknown_returns_default():
    assert parse_category("банан") == "другое"


def test_parse_category_none():
    assert parse_category(None) == "другое"


def test_parse_category_sentence():
    assert parse_category("Эта задача относится к категории Обучение.") == "обучение"


# ---------- parse_minutes ----------
def test_parse_minutes_just_number():
    assert parse_minutes("45") == 45


def test_parse_minutes_with_text():
    assert parse_minutes("Примерно 25 минут") == 25


def test_parse_minutes_none_default():
    assert parse_minutes(None) == 30


def test_parse_minutes_no_digits_default():
    assert parse_minutes("не знаю") == 30


def test_parse_minutes_capped():
    # больше суток — обрезается
    assert parse_minutes("99999") == 60 * 24


# ---------- parse_subtasks ----------
def test_parse_subtasks_standard_format():
    raw = "1. Спланировать\n2. Сделать\n3. Проверить"
    assert parse_subtasks(raw) == ["Спланировать", "Сделать", "Проверить"]


def test_parse_subtasks_with_dashes():
    raw = "- первое\n- второе\n- третье\n- четвёртое"
    # лимит — 3 штуки
    assert parse_subtasks(raw) == ["первое", "второе", "третье"]


def test_parse_subtasks_empty():
    assert parse_subtasks("") == []
    assert parse_subtasks(None) == []
