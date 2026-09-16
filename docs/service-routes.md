# Карта маршрутов сервисов — ГОСТ Analyzer

Часть задачи **DO-01** (вместе с Backend Dockerfile).  
Фиксирует **порты, health и кто куда ходит**, чтобы при контейнеризации не путаться.

Источник по локальным портам: `backend/.env.example` и рабочие конфиги.  
При расхождении с отдельными README (у Doc Service местами указан порт `8001`) приоритет у этой карты.

Отдельный сервис `database` и volumes — этап **DO-05 / DO-07**, здесь только пометка «куда».

---

## Схема

```text
Браузер (:3000)
   │
   ▼
Frontend
   │  только Backend
   ▼
Backend (:8002)
   ├──► Doc Service (:8000)
   │         └──► ML Service (:8001)  (опционально)
   ├──► ML Service (:8001)
   │         └──► Ollama (:11434)
   └──► БД (сейчас у Backend локально SQLite; в Compose — сервис database, DO-05)
```

Frontend **не** ходит в Doc/ML напрямую.

---

## Порты (локальная связка)

| Сервис | Каталог | Порт | Health |
|---|---|---|---|
| Frontend | `frontend/` | `3000` | UI `/` |
| Backend | `backend/` | `8002` | `GET /health` |
| Doc Service | `doc-service/` | `8000` | `GET /documents/health` |
| ML Service | `ml-service/` | `8001` | `GET /health` |
| Ollama | — | `11434` | `GET /api/tags` |
| БД | — | `5432` (если Postgres) | `pg_isready` |

Шпаргалка: **Doc 8000 → ML 8001 → Backend 8002**, Frontend **3000**.

---

## URL между сервисами

### Локально (сейчас)

```text
Frontend  → Backend:     http://127.0.0.1:8002
Backend   → Doc:         http://127.0.0.1:8000
Backend   → ML:          http://127.0.0.1:8001
Doc       → ML:          http://127.0.0.1:8001
ML        → Ollama:      http://127.0.0.1:11434
Backend   → БД:          sqlite:///./app.db   (как в .env.example)
```

### Compose (план DO-05, hostname’ы)

```text
frontend  → backend:8002
backend   → doc-service:8000
backend   → ml-service:8001
doc-service → ml-service:8001
ml-service  → ollama:11434
backend   → db:5432          # после согласования с Backend
```

Имена контейнеров для Compose: `frontend`, `backend`, `doc-service`, `ml-service`, `db`, `ollama`.

---

## Ключевые маршруты Backend (для UI)

```text
/health
/auth/*
/projects/*
/tasks/*
/storage/*
```

В dev Vite проксирует их на `:8002`.

Backend → Doc: `/documents/health`, `/documents/extract`, `/documents/apply_ml_changes`, download.  
Backend → ML: `/health`, `/analyze`.

---

## Переменные (не секретные)

| Переменная | Где | Локально сейчас |
|---|---|---|
| `DOC_SERVICE_BASE_URL` | Backend | `http://127.0.0.1:8000` |
| `ML_SERVICE_BASE_URL` | Backend | `http://127.0.0.1:8001` |
| `BACKEND_PUBLIC_URL` | Backend | `http://127.0.0.1:8002` |
| `ML_SERVICE_URL` | Doc | `http://127.0.0.1:8001` |
| `OLLAMA_BASE_URL` | ML | `http://localhost:11434` |
| `DATABASE_URL` | Backend | `sqlite:///./app.db` |
| `CORS_ORIGINS` | Backend | `http://localhost:3000,...` |

`BACKEND_PUBLIC_URL` нужен, чтобы ML/Doc качали картинки по HTTP с Backend. В Compose значение должно резолвиться **из сети контейнеров** (не `localhost` внутри другого контейнера) — уточним на DO-05.

---

## Зоны ответственности по БД

- Схема/модели/миграции/auth — **Backend (С)**.
- Контейнер `database` и volume данных — **DevOps (Ч), DO-05 / DO-07**.
- Текущий SQLite — локальный режим Backend; это **не** финальное решение Compose.

---

## Порядок DevOps

```text
DO-01  карта маршрутов + Backend Dockerfile   ← сейчас
DO-02  Doc Service Dockerfile
DO-03  ML Service Dockerfile
DO-04  Frontend Dockerfile
DO-05  Compose (+ database — с Backend)
DO-06  Healthchecks
DO-07  Volumes
DO-08  CI
```
