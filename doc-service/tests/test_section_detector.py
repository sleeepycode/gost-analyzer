"""Тесты эвристик section_detector."""
from __future__ import annotations

import pytest

from app.services.section_detector import (
    detect_section,
    is_heading,
    normalize_heading,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Введение", "introduction"),
        ("введение", "introduction"),
        ("Цель работы", "introduction"),
        ("Теоретическая часть", "theory"),
        ("Теория", "theory"),
        ("Практическая часть", "practice"),
        ("Ход работы", "practice"),
        ("Заключение", "conclusion"),
        ("Выводы", "conclusion"),
        ("Список литературы", "bibliography"),
        ("Литература", "bibliography"),
    ],
)
def test_detect_section_known(text: str, expected: str) -> None:
    assert detect_section(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Обычный текст без заголовка",
        "Случайная строка",
        "a" * 200,  # слишком длинная
    ],
)
def test_detect_section_unknown(text: str) -> None:
    assert detect_section(text) is None


def test_detect_section_with_leading_number() -> None:
    assert detect_section("1. Введение") == "introduction"
    assert detect_section("2.3. Практическая часть") == "practice"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Введение", True),
        ("1. Введение", True),
        ("ТЕОРЕТИЧЕСКАЯ ЧАСТЬ", True),
        ("Методика:", True),
        ("Это длинное предложение с точкой в конце, которое не является заголовком.", False),
        ("", False),
    ],
)
def test_is_heading(text: str, expected: bool) -> None:
    assert is_heading(text) is expected


def test_normalize_heading_strips_numbering() -> None:
    assert normalize_heading("1. Введение") == "Введение"
    assert normalize_heading("2.3. Практическая часть") == "Практическая часть"
    assert normalize_heading("Введение") == "Введение"
    assert normalize_heading("  Введение  ") == "Введение"