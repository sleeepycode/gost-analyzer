Фронтенд подключён к основному backend: http://127.0.0.1:8002

Запуск фронтенда:
1) cd Designer_Lab-frontend
2) npm install
3) npm run dev
4) открыть http://127.0.0.1:3000

В .env уже прописано:
VITE_API_BASE_URL=http://127.0.0.1:8002

Проверка:
- основной backend должен быть на 8002
- doc-service должен быть на 8000
- ML должен быть на 8001
- Ollama должен быть на 11434

Если фронтенд не видит backend, проверь VITE_API_BASE_URL и перезапусти npm run dev.
