# Инструкция по настройке ML-модуля

## 1. Python

Рекомендуется Python 3.10–3.12.

Для PaddleOCR лучше не использовать Python 3.14.

## 2. Создать виртуальное окружение

```bash
py -3.11 -m venv .venv
```

Активация PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Если PowerShell запрещает запуск:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

## 3. Установить зависимости

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Установить Ollama

Скачать Ollama:

https://ollama.com

Скачать модель:

```bash
ollama pull llama3.2:3b
```

Для слабого ПК:

```bash
ollama pull qwen2.5:1.5b
```

## 5. Создать `.env`

В корне проекта:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Если надо запустить без LLM:

```env
AI_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## 6. Проверить Ollama

```bash
python test_ollama.py
```

## 7. Проверить OCR fallback

```bash
python test_ocr_fallback.py
```

Сценарии:

```text
PaddleOCR работает → используется PaddleOCR
PaddleOCR падает → используется EasyOCR
EasyOCR тоже падает → возвращается пустой OCR-текст, backend не падает
```

## 8. Полный тест

```bash
python test_ml.py
```

## 9. Тест payload для backend

```bash
python test_payload.py
```

## 10. Главный импорт

```python
from ml.service import analyze_project
```

```python
ml_result = analyze_project(
    document_text=document_text,
    image_paths=image_paths,
    topic=topic
)
```

## 11. Исправление смешивания языков Ollama

В этой версии усилена генерация на русском:

- строгий system prompt;
- temperature = 0.1;
- JSON-only ответ;
- все текстовые значения должны быть на русском;
- добавлен `ml/language_guard.py`;
- частые английские слова заменяются на русские аналоги.
