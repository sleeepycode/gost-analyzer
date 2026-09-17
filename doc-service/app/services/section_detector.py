from __future__ import annotations

import re


_NUMBERING_RE = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s*")
# Маппинг «что встретили в тексте» -> «какой это раздел»
SECTION_PATTERNS: list[tuple[str, str]] = [
    ("introduction", r"^\s*введение\b"),
    ("introduction", r"^\s*цель работы\b"),
    ("introduction", r"^\s*цель лабораторной\b"),
    ("theory", r"^\s*теоретическая часть\b"),
    ("theory", r"^\s*теоретические сведения\b"),
    ("theory", r"^\s*теория\b"),
    ("practice", r"^\s*практическая часть\b"),
    ("practice", r"^\s*ход работы\b"),
    ("practice", r"^\s*выполнение работы\b"),
    ("practice", r"^\s*экспериментальная часть\b"),
    ("practice", r"^\s*задание\b"),
    ("conclusion", r"^\s*заключение\b"),
    ("conclusion", r"^\s*выводы\b"),
    ("conclusion", r"^\s*вывод\b"),
    ("bibliography", r"^\s*список литературы\b"),
    ("bibliography", r"^\s*литература\b"),
    ("bibliography", r"^\s*библиографический список\b"),
]

_COMPILED = [(key, re.compile(pattern, re.IGNORECASE)) for key, pattern in SECTION_PATTERNS]

MAX_HEADING_LEN = 120




def detect_section(text: str) -> str | None:
    if not text:
        return None
    normalized = text.strip()
    if len(normalized) > MAX_HEADING_LEN:
        return None

    # Убираем нумерацию в начале: "1. Введение" -> "Введение"
    stripped = _NUMBERING_RE.sub("", normalized).strip()

    for key, pattern in _COMPILED:
        if pattern.search(stripped) or pattern.search(normalized):
            return key
    return None


def is_heading(text: str) -> bool:
    """
    Эвристика «это заголовок».

    Признаки:
    - совпадает с известной секцией;
    - короткая строка в верхнем регистре;
    - заканчивается двоеточием и короткая;
    - начинается с «N. Название» (нумерованный раздел).
    """
    if not text:
        return False
    normalized = text.strip()
    if not normalized or len(normalized) > MAX_HEADING_LEN:
        return False

    if detect_section(normalized):
        return True

    # 1. Введение / Заключение и т.п. одной строкой
    if normalized.isupper() and len(normalized.split()) <= 8:
        return True

    # 2. "1. Введение", "2.3. Методика"
    if re.match(r"^\d+(\.\d+)*\.?\s+\S", normalized):
        return True

    # 3. Короткая строка с двоеточием в конце
    if len(normalized) < 80 and normalized.endswith(":"):
        return True

    return False


def normalize_heading(text: str) -> str:
    """Чистит заголовок: убирает нумерацию, лишние пробелы."""
    if not text:
        return ""
    cleaned = re.sub(r"^\d+(\.\d+)*\.?\s+", "", text.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()