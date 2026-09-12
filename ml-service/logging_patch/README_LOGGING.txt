
# Как подключить логи

1. Скопировать logger.py в:

ml/logger.py

2. Импортировать:

from ml.logger import logger

3. Добавить логи в:
- app/main.py
- ml/service.py
- ml/image_source.py
- ml/ocr.py
- ml/image_analyzer.py
- ml/ollama_client.py

# Что логировать

## API
- старт сервера
- входящий запрос
- project_id
- количество изображений

## Image download
- URL картинки
- успешное скачивание
- ошибка скачивания

## OCR
- старт OCR
- пустой OCR
- ошибки OCR

## Classification
- тип изображения
- fallback classification

## AI
- запрос к Ollama
- fallback AI
- invalid JSON

## Pipeline
- успешное завершение
- partial result
- error result
