# API Contract

## Request
```json
{"document_text":"string","image_paths":["string"],"topic":"string"}
```

## Response
```json
{
  "success": true,
  "topic": "string",
  "summary": {"status":"ready | needs_review | error","missing_sections_count":0,"images_count":0,"suggestions_count":0},
  "report": {"found_sections":[],"missing_sections":[],"has_required_structure":false,"generated_sections":[],"bibliography":[]},
  "images": [],
  "content_suggestions": [],
  "errors": [],
  "meta": {"module":"ofor-ml","version":"9.0-api-ready-local-ai","approach":"local-llm-first-safe-fallback","ai_provider":"ollama","ai_used":true}
}
```


## Передача изображений по URL

ML поддерживает два варианта передачи изображений:

1. Локальные/shared пути:

```json
{
  "image_paths": [
    "storage/projects/123/images/graph.png"
  ]
}
```

2. HTTP/HTTPS ссылки:

```json
{
  "image_urls": [
    "http://backend:8000/storage/projects/123/images/graph.png"
  ]
}
```

Также URL можно передать в расширенном формате:

```json
{
  "images": [
    {
      "image_id": "img_001",
      "path": "http://backend:8000/storage/projects/123/images/graph.png",
      "source": "back1_user_upload"
    }
  ]
}
```

Внутри ML URL временно скачивается в локальный файл, после чего обрабатывается PaddleOCR/EasyOCR. В ответе ML сохраняет исходный `path`/URL, чтобы backend мог понимать, какой файл анализировался.
