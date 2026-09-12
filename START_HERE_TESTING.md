# Локальный запуск всей связки

В этом архиве backend уже переведен на SQLite. PostgreSQL больше не нужен.

Порты:
- Doc Service: 8000
- ML Service: 8001
- Main Backend: 8002
- Frontend: 3000
- Ollama: 11434

## 1. Ollama

```powershell
ollama serve
```

В другом терминале:

```powershell
ollama pull qwen2.5:3b
ollama list
curl http://127.0.0.1:11434/api/tags
```

## 2. ML Service

```powershell
cd AI_model_fixed
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info
```

`AI_model_fixed/.env` уже есть. Важные значения:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
USE_OLLAMA=true
IMAGE_ANALYSIS_MODE=fast
MAX_OCR_IMAGES=0
ENABLE_IMAGE_AI=false
```

## 3. Doc Service

```powershell
cd Designer_Lab-Doc-Service-fixed
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

`Designer_Lab-Doc-Service-fixed/.env` уже есть.

## 4. Main Backend на SQLite

```powershell
cd Designer_Lab-backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8002 --log-level info
```

`Designer_Lab-backend/.env` уже создан и содержит:

```env
DATABASE_URL=sqlite:///./app.db
```

Файл базы создастся автоматически:

```text
Designer_Lab-backend/app.db
```

Если нужно сбросить базу:
1. Останови backend.
2. Удали `Designer_Lab-backend/app.db`.
3. Запусти backend снова.

## 5. Frontend

```powershell
cd Designer_Lab-frontend
npm install
npm run dev
```

Открыть:

```text
http://127.0.0.1:3000
```

Фронт уже настроен на основной backend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8002
```

## 6. Проверка

Открой:

```text
http://127.0.0.1:8002/docs
```

Сначала загрузи DOCX:

```text
POST /projects/upload
```

Потом при необходимости загрузи пользовательскую картинку:

```text
POST /projects/{project_id}/files
```

Итоговый файл:

```text
GET /projects/{project_id}/download?user_id=test_user_001
```

Если статус проекта только `uploaded`, значит нужно запустить endpoint обработки проекта во вкладке Swagger, например `/projects/{project_id}/process`, если он есть в текущей версии backend.
