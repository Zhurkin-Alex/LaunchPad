# Аналитика российских акций

Веб-приложение для анализа российского фондового рынка. Бэкенд — FastAPI + MOEX ISS API. Фронтенд — React 18 + TypeScript + Tailwind CSS (Vite).

## Возможности

- **Анализ портфеля** — вводите тикеры вручную или загружайте PDF/изображение; получаете геориск, Долг/EBITDA, ROE, дивиденды, free-float, новостной фон и живую цену с MOEX
- **DCA-калькулятор** — симуляция регулярных покупок с 2010 года по любым тикерам; результат с дивидендами и без; детальная история покупок
- **Лучшие акции** — динамическая подборка лучших акций MOEX по суммарному CAGR (цена + дивиденды) с балансировкой по секторам; симулятор доходности с графиком

---

## Быстрый старт

### 1. Бэкенд (FastAPI)

```bash
cd /путь/к/проекту

# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить (с Redis или без)
uvicorn main:app --reload
```

Бэкенд запустится на `http://localhost:8000`.

> **Redis** (опционально) — если недоступен, сессии хранятся в памяти:
> ```bash
> brew install redis && brew services start redis   # macOS
> docker run -d -p 6379:6379 redis:7-alpine         # Docker
> ```

> **EasyOCR** тянет PyTorch (~2 ГБ). При первом запуске OCR-модели скачаются автоматически (~300 МБ). Если OCR не нужен, можно опустить `easyocr` из зависимостей.

### 2. Фронтенд (React + Vite)

```bash
cd frontend

# Требуется Bun (https://bun.sh)
# Установка: curl -fsSL https://bun.sh/install | bash

bun install
bun run dev
```

Фронтенд запустится на `http://localhost:5173` и будет проксировать все `/api/*` запросы на бэкенд.

---

## Структура проекта

```
.
├── main.py              # FastAPI: эндпоинты, CORS, сессии
├── analyzer.py          # Аналитика тикеров, сводка портфеля
├── backtest.py          # DCA-симулятор (покупки + дивиденды)
├── data_fetcher.py      # MOEX ISS API: цены, дивиденды, список акций
├── portfolio.py         # Умный портфель: метрики, фильтрация, Chart.js-серии
├── parsers.py           # Извлечение тикеров из PDF и изображений (OCR)
├── companies.json       # Статичная база ~20 компаний (фолбэк)
├── requirements.txt
└── frontend/            # React-приложение (Vite)
    ├── src/
    │   ├── api/         # types.ts, client.ts
    │   ├── store/       # Zustand store
    │   ├── utils/       # format.ts (fmtRub, fmtPct, …)
    │   └── components/
    │       ├── layout/  # Hero, NavTabs, Disclaimer
    │       ├── ui/      # Toast, Spinner, SectorBadge, TickerTagInput, DropZone
    │       ├── charts/  # PortfolioChart (Chart.js)
    │       └── tabs/    # AnalyticsTab, DcaTab, TopStocksTab
    ├── tailwind.config.js
    └── vite.config.ts   # proxy /api → localhost:8000
```

---

## API

| Метод  | Путь                       | Описание |
|--------|----------------------------|----------|
| `POST` | `/api/upload`              | Загрузить PDF/PNG/JPG → найденные тикеры |
| `POST` | `/api/analyze`             | `{"tickers": ["SBER","GAZP"]}` → аналитика + session_id |
| `GET`  | `/api/session/{id}`        | Сохранённый результат (хранится 24 ч) |
| `POST` | `/api/backtest`            | DCA-расчёт: `{tickers, start_year, amount, frequency}` |
| `GET`  | `/api/backtest/tickers`    | Список доступных тикеров для DCA |
| `GET`  | `/api/smart-portfolio`     | Динамическая подборка лучших акций MOEX `?years=5&min_cagr=12` |
| `POST` | `/api/portfolio-chart`     | Chart.js-серии для симулятора: `{tickers, weights, start_year, amount, frequency}` |

---

## Технологии

| Слой      | Стек |
|-----------|------|
| Бэкенд    | Python 3.11+, FastAPI, httpx, pdfplumber, easyocr, Redis |
| Данные    | MOEX ISS API (цены, история, дивиденды, список акций) |
| Фронтенд  | React 18, TypeScript, Vite, Tailwind CSS 3, Bun |
| Состояние | Zustand, TanStack Query |
| Графики   | Chart.js + react-chartjs-2 |

---

## Примечания

- **Данные MOEX** кешируются в памяти: цены — 1 ч, история/дивиденды — 24 ч, список акций — 1 ч
- **Умный портфель** анализирует ~80–120 акций MOEX (листинг 1–2 уровня) — запрос занимает 20–60 с
- **Сессии без Redis** хранятся только в памяти процесса и теряются при перезапуске
- **Лимиты**: PDF — 20 страниц, изображения — 2 МП, файлы — 50 МБ, тикеров за запрос — 50

---

> ⚠️ Только в образовательных целях. Не является инвестиционной рекомендацией.
