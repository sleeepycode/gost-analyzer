# Frontend — зависимости и запуск

## Что нужно установить на компьютер

| Инструмент | Версия |
|------------|--------|
| **Node.js** | 18.x или 20.x LTS (с npm) |
| **npm** | идёт вместе с Node.js |

Проверка:

```bat
node -v
npm -v
```

## Все npm-пакеты проекта

Устанавливать **одной командой** из папки `frontend/`:

```bat
npm install
```

или двойной клик по `install.cmd`.

Список пакетов — в `requirements-frontend.txt` и в `package.json` / `package-lock.json`.

### Production (нужны для работы приложения)

| Пакет | Назначение |
|-------|------------|
| react | UI |
| react-dom | Рендер React |
| react-router-dom | Маршруты (страницы) |
| docx-preview | Превью DOCX в браузере |

### Dev (нужны для сборки и разработки)

| Пакет | Назначение |
|-------|------------|
| vite | Сборщик и dev-сервер |
| @vitejs/plugin-react | React в Vite |
| typescript | Типы TS |
| tailwindcss | Стили |
| postcss | CSS pipeline |
| autoprefixer | Префиксы CSS |
| @types/react, @types/react-dom | Типы для React |

## Запуск

### Вариант A — UI на том же порту, что backend (как у нас сейчас)

1. Поднять backend на **8002** (Doc-Service :8000, ML :8001).
2. Собрать фронт:
   ```bat
   npm run build
   ```
3. Открыть **http://127.0.0.1:8002** (статику раздаёт backend).

### Вариант B — отдельный dev-сервер Vite (:3000)

```bat
npm run dev
```

Прокси на API — в `vite.config.ts` (target `http://127.0.0.1:8002`).

## Переменные окружения (опционально)

Файл `.env` (можно скопировать из `.env.example`):

```env
# Обычно не нужен: API на том же origin (8002)
# VITE_API_BASE_URL=http://127.0.0.1:8002
```

Если фронт на :3000, а backend на :8002 — можно задать `VITE_API_BASE_URL=http://127.0.0.1:8002`.

## Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `npm` не найден | Установить Node.js LTS |
| `ECONNREFUSED` при логине | Запустить backend :8002 |
| Пустая страница после build | Пересобрать: `npm run build`, перезапустить backend |
| Старые пакеты | Удалить `node_modules`, снова `npm install` |

## Файлы, которые не коммитят в git

- `node_modules/`
- `dist/` (результат `npm run build`)
- `.env` (локальные настройки)
