from ml.logger import logger
import requests

from ml.config import OLLAMA_BASE_URL, OLLAMA_MODEL, is_ollama_enabled


STRICT_RUSSIAN_SYSTEM_PROMPT = """
Ты AI-модуль для анализа русскоязычных учебных отчётов.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Отвечай только на русском языке.
2. Не используй английский язык в значениях JSON, кроме технических ключей.
3. Не используй markdown.
4. Не добавляй пояснения вокруг JSON.
5. Возвращай только валидный JSON.
6. Если нужно сгенерировать текст раздела, текст должен быть полностью на русском языке.
7. Если нужно сгенерировать подпись, подпись должна быть полностью на русском языке.
8. Если не уверен — всё равно верни корректный JSON на русском языке.
"""

def ask_ollama_json(
    prompt: str,
    system_prompt: str = "Ты полезный AI-анализатор учебных отчётов.",
) -> str:

    if not is_ollama_enabled():
        raise RuntimeError(
            "Ollama is not enabled. Set AI_PROVIDER=ollama."
        )

    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"

    full_prompt = (
        STRICT_RUSSIAN_SYSTEM_PROMPT
        + "\n\n"
        + system_prompt
        + "\n\n"
        + prompt
        + "\n\n"
        + "Верни только валидный JSON. "
        + "Не добавляй markdown. "
        + "Все текстовые значения должны быть на русском языке."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "repeat_penalty": 1.1,
        },
    }

    logger.info(
        f"Sending request to Ollama model={OLLAMA_MODEL} url={url}"
    )

    response = requests.post(
        url,
        json=payload,
        timeout=180
    )

    logger.info(
        f"Ollama response status={response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    content = data.get("response", "")

    if not content:
        raise RuntimeError(
            f"Ollama returned empty response: {data}"
        )

    logger.info(
        f"Ollama response received len={len(content)}"
    )

    return content

