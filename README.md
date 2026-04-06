# Аналитика российских акций — MVP

Веб-приложение на FastAPI: загружаете PDF / изображение или вводите тикеры вручную, получаете информационную аналитику (геориск, Долг/EBITDA, ROE, дивиденды, free-float, новостной фон) и ссылку для отправки.

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

> ⚠️ **EasyOCR** тянет PyTorch (~2 ГБ). При первом запуске OCR модели скачаются автоматически (~300 МБ).  
> Если OCR не нужен — можно пропустить: `pip install fastapi uvicorn[standard] jinja2 python-multipart pdfplumber Pillow pydantic`.

### 2. Запуск

**Без Redis** (сессии хранятся в памяти процесса):
```bash
uvicorn main:app --reload
```

**С Redis** (сессии живут 24 ч, рекомендуется для продакшена):
```bash
# macOS
brew install redis && brew services start redis

# Linux
sudo apt install redis-server && sudo systemctl start redis

# Docker (любая платформа)
docker run -d -p 6379:6379 redis:7-alpine

# Затем запустить приложение
uvicorn main:app --reload
```

### 3. Открыть в браузере

```
http://localhost:8000
```

---

## Структура проекта

```
.
├── main.py           # FastAPI: эндпоинты, хранение сессий
├── parsers.py        # Извлечение текста из PDF, OCR изображений, поиск тикеров
├── analyzer.py       # Аналитика по тикерам, сводка портфеля
├── companies.json    # База данных 20 российских компаний
├── templates/
│   └── index.html   # Фронтенд — Bootstrap 5, drag-&-drop, AJAX
└── requirements.txt
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET`  | `/` | Главная страница |
| `POST` | `/api/upload` | Загрузить PDF/PNG/JPG → вернуть найденные тикеры |
| `POST` | `/api/analyze` | `{"tickers": ["SBER","GAZP"]}` → аналитика + session_id |
| `GET`  | `/api/session/{id}` | Получить сохранённый результат (живёт 24 ч) |

## Поддерживаемые тикеры (20 компаний)

`SBER` `GAZP` `LKOH` `GMKN` `YDEX` `MGNT` `MTSS` `ROSN` `TATN` `VTBR`  
`NVTK` `SNGS` `PHOR` `PLZL` `CHMF` `AFLT` `X5` `OZON` `TCSG` `MOEX`

## Примечания

- **Данные оценочные** — компания и аналитические значения в `companies.json` подобраны правдоподобно, но не являются актуальными рыночными данными.
- **Сессии без Redis** хранятся только в памяти текущего процесса и теряются при перезапуске.
- **OCR** работает только с `easyocr`. При первом вызове инициализация занимает ~15–30 с.
- **Лимиты**: PDF — 20 страниц, изображения — 2 МП, файлы — 50 МБ, тикеров за запрос — 50.

---

> ⚠️ Информация носит ознакомительный характер и **не является инвестиционной рекомендацией**.
