from __future__ import annotations

import json
from ml.service import analyze_project


def main() -> None:
    document_text = """
    Введение

    Цель работы — разработать ML-модуль анализа и оформления учебных отчётов.

    Практическая часть

    В ходе работы был реализован pipeline анализа структуры документа и обработки изображений.

    Заключение

    В результате работы был создан модуль, возвращающий структурированный JSON для backend.
    """

    result = analyze_project(
        document_text=document_text,
        image_paths=[],
        topic="ML-модуль оформления отчётов",
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
