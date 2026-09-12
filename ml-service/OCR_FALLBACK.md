# OCR fallback: PaddleOCR → EasyOCR

OCR-слой работает независимо от AI/Ollama.

## Схема

```text
image
  ↓
PaddleOCR
  ↓ если ошибка или пустой текст
EasyOCR
  ↓ если ошибка или пустой текст
пустой OCR-текст, backend не падает
```

## Сценарии

### 1. Всё работает

```text
PaddleOCR ✅ + Ollama ✅
```

Используется PaddleOCR, затем Ollama анализирует OCR-текст.

### 2. PaddleOCR упал

```text
PaddleOCR ❌ → EasyOCR ✅ + Ollama ✅
```

Ollama продолжает работать. Падение OCR-движка не отключает AI.

### 3. Ollama упала

```text
PaddleOCR ✅ + Ollama ❌ → локальный AI fallback
```

OCR работает, смысловой анализ уходит в fallback.

### 4. Всё упало

```text
PaddleOCR ❌ → EasyOCR ❌ → пустой OCR-текст
Ollama ❌ → fallback
```

Система возвращает JSON и не роняет backend.

## Почему так

PaddleOCR мощнее для документов, таблиц и сканов, но сложнее в установке.
EasyOCR проще и стабильнее как резерв.
