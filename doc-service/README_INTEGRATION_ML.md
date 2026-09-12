# Doc Service → ML integration

## Запуск

Doc Service:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
```

ML Service:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload --log-level info
```

## .env Doc Service

```env
SERVICE_URL=http://127.0.0.1:8000
ML_SERVICE_URL=http://127.0.0.1:8001
ML_TIMEOUT=240
```

## Что исправлено

Doc Service теперь отправляет в ML правильный контракт:

```json
{
  "project_id": "...",
  "document_text": "склеенный текст paragraphs[]",
  "image_paths": [],
  "image_urls": [],
  "images": [
    {
      "image_id": "image_1",
      "path": "http://127.0.0.1:8000/storage/projects/.../media/image1.png",
      "source": "original_docx_image"
    }
  ],
  "topic": "..."
}
```

## Проверка

1. Загрузить DOCX через:

```text
POST /documents/extract-and-analyze
```

2. Проверить payload:

```text
GET /documents/debug-ml-payload/{project_id}
```

3. Проверить картинку в браузере:

```text
http://127.0.0.1:8000/storage/projects/{project_id}/media/image1.png
```

Если картинка открывается, ML сможет скачать её по URL.
