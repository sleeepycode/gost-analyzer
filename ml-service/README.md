# AI_model — ML-модуль анализа отчётов

Модуль принимает текст отчёта и изображения, анализирует структуру документа, OCR-текст изображений, типы картинок, подписи и возвращает JSON для backend.

## Что исправлено в этой версии

- Добавлен полноценный FastAPI входной файл: `app/main.py`.
- Добавлен запуск через `uvicorn app.main:app`.
- Добавлен `run_example.py` для проверки без backend.
- Добавлен `/health` endpoint.
- Добавлен главный endpoint `POST /analyze`.
- Добавлены вспомогательные endpoint'ы: `/ocr`, `/classify-image`, `/analyze-structure`, `/generate-caption`.
- Добавлена поддержка двух форматов картинок:
  - `image_paths: ["..."]`
  - `images: [{"path": "...", "source": "back1_user_upload"}]`
- В ответ добавляется инструкция `insert`, чтобы backend вставлял именно изображение, а не OCR-текст.

---

## Установка

Рекомендуется Python 3.12.

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\activate
```

Установка зависимостей:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Настройка Ollama

Установи Ollama и скачай модель:

```bash
ollama pull llama3.2:3b
```

Создай `.env` на основе `.env.example`:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Если нужно запустить без Ollama, поставь:

```env
AI_PROVIDER=none
```

Тогда модуль будет использовать fallback-логику.

---

## Быстрая проверка без backend

```bash
python run_example.py
```

---

## Запуск API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

Health check:

```text
GET http://127.0.0.1:8001/health
```

---

## Главный запрос backend к ML

Endpoint:

```http
POST /analyze
```

Минимальный request:

```json
{
  "project_id": "123",
  "document_text": "Введение... Практическая часть... Заключение...",
  "image_paths": [
    "storage/projects/123/images/graph.png"
  ],
  "topic": "Лабораторная работа"
}
```

Расширенный request:

```json
{
  "project_id": "123",
  "document_text": "Введение... Практическая часть... Заключение...",
  "topic": "Лабораторная работа",
  "images": [
    {
      "image_id": "img_001",
      "path": "storage/projects/123/images/user_graph.png",
      "source": "back1_user_upload"
    },
    {
      "image_id": "img_002",
      "path": "storage/projects/123/images/from_docx_001.png",
      "source": "back2_parsed_from_docx"
    }
  ]
}
```

Пример response:

```json
{
  "success": true,
  "project_id": "123",
  "status": "needs_review",
  "found_sections": ["introduction", "practice", "conclusion"],
  "missing_sections": ["theory", "references"],
  "images": [
    {
      "image_id": "img_001",
      "path": "storage/projects/123/images/user_graph.png",
      "source": "back1_user_upload",
      "type": "graph",
      "ocr_text": "Температура Время",
      "caption": "Рисунок 1 — График зависимости температуры",
      "placement": {
        "paragraph_index": 3,
        "score": 0.8,
        "reason": "Подходит к практической части"
      },
      "insert": {
        "enabled": true,
        "mode": "image",
        "target_section": "practice",
        "caption": true,
        "caption_position": "below",
        "ocr_text_as_note": false,
        "width_cm": 12
      }
    }
  ]
}
```

Важно для backend: `ocr_text` не нужно вставлять вместо картинки. Для вставки используется `path`, а `ocr_text` нужен только для анализа.

---

## Все endpoint'ы

```text
GET  /health
POST /analyze
POST /analyze-structure
POST /ocr
POST /classify-image
POST /generate-caption
```


## Передача картинок с другого хоста backend

ML умеет работать с тремя вариантами изображений:

1. Локальный путь, если backend и ML видят одну файловую систему:

```json
{
  "image_paths": ["storage/projects/123/images/graph.png"]
}
```

2. Полный URL до картинки на backend:

```json
{
  "image_urls": ["http://127.0.0.1:8000/storage/projects/123/images/graph.png"]
}
```

3. Относительный backend storage path. Для этого нужно указать `BACKEND_BASE_URL`:

```env
BACKEND_BASE_URL=http://127.0.0.1:8000
```

Тогда backend может отправлять:

```json
{
  "images": [
    {
      "image_id": "img_001",
      "path": "/storage/projects/123/images/graph.png",
      "source": "back2_parsed_from_docx"
    }
  ]
}
```

ML соберёт полный URL:

```text
http://127.0.0.1:8000/storage/projects/123/images/graph.png
```

и скачает изображение через `requests.get()` в файле:

```text
ml/image_source.py
```

На стороне backend картинка должна реально открываться в браузере по URL. Например для FastAPI backend:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/storage", StaticFiles(directory="storage"), name="storage")
```

После этого URL вида:

```text
http://127.0.0.1:8000/storage/projects/123/images/graph.png
```

будет доступен ML-сервису.
