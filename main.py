# main.py
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analyzer import analyze_portfolio, _get_companies
from backtest import run_dca
from data_fetcher import (
    enrich_tickers, fetch_dividends_data, fetch_price_history,
    fetch_prices, fetch_moex_all_stocks,
)
from parsers import extract_text_from_pdf, extract_text_from_image, extract_tickers
from portfolio import build_chart_series, build_dynamic_portfolio

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Russian Stock Analyzer MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Хранение сессий: Redis → fallback на in-memory dict ──────────────────────

SESSION_TTL = 86_400  # 24 часа

try:
    import redis as _redis_lib

    _redis_client = _redis_lib.Redis(
        host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=2
    )
    _redis_client.ping()
    USE_REDIS = True
    logger.info("Хранилище сессий: Redis")
except Exception:
    USE_REDIS = False
    _mem_store: dict[str, dict] = {}
    _mem_ts: dict[str, float] = {}
    logger.info("Redis недоступен — используется in-memory хранилище")


def _session_save(session_id: str, data: dict) -> None:
    if USE_REDIS:
        _redis_client.setex(
            session_id, SESSION_TTL, json.dumps(data, ensure_ascii=False)
        )
    else:
        _mem_store[session_id] = data
        _mem_ts[session_id] = time.time()
        _cleanup_memory()


def _session_get(session_id: str) -> Optional[dict]:
    if USE_REDIS:
        raw = _redis_client.get(session_id)
        return json.loads(raw) if raw else None
    ts = _mem_ts.get(session_id)
    if ts and time.time() - ts < SESSION_TTL:
        return _mem_store.get(session_id)
    return None


def _cleanup_memory() -> None:
    """Удаляет просроченные in-memory сессии."""
    now = time.time()
    expired = [k for k, ts in _mem_ts.items() if now - ts > SESSION_TTL]
    for k in expired:
        _mem_store.pop(k, None)
        _mem_ts.pop(k, None)


# ── Модели запросов ───────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    tickers: list[str]


class BacktestRequest(BaseModel):
    tickers:    list[str]  # один или несколько тикеров MOEX
    start_year: int        # 2010–текущий год
    amount:     float      # сумма одной закупки в рублях на тикер
    frequency:  str        # "once" | "monthly" | "weekly"


# ── Эндпоинты ─────────────────────────────────────────────────────────────────


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    Принимает PDF или изображение, возвращает найденные тикеры.
    Лимит: 50 МБ, PDF — 20 страниц, изображения — 2 МП.
    """
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 50 МБ)")

    is_pdf = "pdf" in content_type or filename.endswith(".pdf")
    is_image = any(
        t in content_type for t in ("image/", "jpeg", "jpg", "png")
    ) or filename.endswith((".jpg", ".jpeg", ".png"))

    if not (is_pdf or is_image):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только PDF и изображения PNG/JPG",
        )

    try:
        if is_pdf:
            text = extract_text_from_pdf(file_bytes)
        else:
            text = extract_text_from_image(file_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Ошибка обработки файла")
        raise HTTPException(
            status_code=500, detail=f"Ошибка обработки файла: {exc}"
        ) from exc

    tickers = extract_tickers(text)
    return {"tickers": tickers, "text_preview": text[:500]}


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest) -> dict:
    """
    Принимает список тикеров, возвращает аналитику + session_id на 24 ч.
    """
    if not body.tickers:
        raise HTTPException(status_code=400, detail="Список тикеров пуст")
    if len(body.tickers) > 50:
        raise HTTPException(status_code=400, detail="Максимум 50 тикеров за один запрос")

    # Дедупликация с сохранением порядка
    seen: set[str] = set()
    tickers: list[str] = []
    for t in body.tickers:
        clean = t.strip().upper()
        if clean and clean not in seen:
            seen.add(clean)
            tickers.append(clean)

    data = analyze_portfolio(tickers)

    # Обогащаем живыми данными MOEX (цена + реальные дивидендные годы)
    found_tickers = [r["ticker"] for r in data["results"] if r["found"]]
    live = await enrich_tickers(found_tickers)

    for result in data["results"]:
        ticker = result["ticker"]
        ld = live.get(ticker, {})

        # Цена
        price = ld.get("price")
        if price is not None:
            result["price"] = f'{price:,.0f} ₽'.replace(",", "\u2009")  # тонкий пробел
            result["price_date"] = ld.get("price_date", "")
            result["price_is_live"] = ld.get("is_live", False)
        else:
            result["price"] = "—"
            result["price_date"] = ""
            result["price_is_live"] = False

        # Дивидендные годы — берём живое значение если MOEX вернул данные
        div_live = ld.get("dividend_years_live")
        if div_live is not None:
            result["dividend_years"] = str(div_live)

    data["live_updated_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    data["live_source"] = "MOEX ISS API"

    session_id = str(uuid.uuid4())
    _session_save(session_id, data)

    return {"session_id": session_id, **data}


@app.post("/api/backtest")
async def backtest(body: BacktestRequest) -> dict:
    """
    DCA-калькулятор для одного или нескольких тикеров.
    Загружает исторические цены и дивиденды параллельно, возвращает
    результаты по каждому тикеру и сводку по всему портфелю.
    """
    if not body.tickers:
        raise HTTPException(400, "Укажите хотя бы один тикер")
    if len(body.tickers) > 20:
        raise HTTPException(400, "Максимум 20 тикеров за один запрос")
    if body.start_year < 2010 or body.start_year > date.today().year:
        raise HTTPException(400, "Год должен быть в диапазоне 2010 — текущий год")
    if body.amount < 100:
        raise HTTPException(400, "Минимальная сумма закупки — 100 ₽")
    if body.frequency not in ("once", "monthly", "weekly"):
        raise HTTPException(400, "frequency должен быть: once | monthly | weekly")

    tickers   = list(dict.fromkeys(t.strip().upper() for t in body.tickers if t.strip()))
    from_date = f"{body.start_year}-01-01"
    till_date = date.today().isoformat()
    companies = _get_companies()

    async def _calc_one(ticker: str) -> dict:
        history, prices_map, dividends = await asyncio.gather(
            fetch_price_history(ticker, from_date, till_date),
            fetch_prices([ticker]),
            fetch_dividends_data(ticker),
        )
        company       = companies.get(ticker, {})
        current_price = prices_map.get(ticker, {}).get("price")  # type: ignore[union-attr]

        if not history:
            return {
                "ticker":  ticker,
                "company": company.get("name", ticker),
                "sector":  company.get("sector", ""),
                "error":   "Нет данных MOEX для указанного периода",
            }

        result = run_dca(history, body.amount, body.frequency, current_price, dividends)
        if "error" in result:
            return {
                "ticker":  ticker,
                "company": company.get("name", ticker),
                "sector":  company.get("sector", ""),
                "error":   result["error"],
            }

        return {
            "ticker":  ticker,
            "company": company.get("name", ticker),
            "sector":  company.get("sector", ""),
            **result,
        }

    results: list[dict] = list(
        await asyncio.gather(*[_calc_one(t) for t in tickers])
    )

    # ── Сводка по всем тикерам ────────────────────────────────────────────────
    valid = [r for r in results if "error" not in r]
    if valid:
        tot_invested  = round(sum(r["summary"]["total_invested"] for r in valid), 2)
        tot_value     = round(sum(r["summary"]["current_value"] or 0 for r in valid), 2)
        tot_div       = round(sum(r["summary"]["total_dividends"] for r in valid), 2)
        tot_pnl       = round(tot_value - tot_invested, 2)
        tot_pnl_div   = round(tot_pnl + tot_div, 2)
        pnl_pct       = round(tot_pnl / tot_invested * 100, 2) if tot_invested else None
        pnl_pct_div   = round(tot_pnl_div / tot_invested * 100, 2) if tot_invested else None
    else:
        tot_invested = tot_value = tot_div = tot_pnl = tot_pnl_div = 0.0
        pnl_pct = pnl_pct_div = None

    return {
        "results": results,
        "combined": {
            "total_invested":   tot_invested,
            "total_value":      tot_value,
            "total_dividends":  tot_div,
            "pnl":              tot_pnl,
            "pnl_pct":          pnl_pct,
            "pnl_with_div":     tot_pnl_div,
            "pnl_pct_with_div": pnl_pct_div,
            "ticker_count":     len(tickers),
            "valid_count":      len(valid),
        },
    }


@app.get("/api/smart-portfolio")
async def smart_portfolio(
    years:    int   = 5,
    min_cagr: float = 8.0,
) -> dict:
    """
    Динамически формирует лучший сбалансированный портфель на основе реальных данных MOEX.
    Анализирует все акции уровня листинга 1-2 на TQBR (обычно 80-120 бумаг),
    сортирует по капитализации, фильтрует по суммарному CAGR.
    """
    # 1. Получаем полный список акций с биржи
    all_stocks = await fetch_moex_all_stocks(max_list_level=2, max_count=120)
    if not all_stocks:
        raise HTTPException(503, "Не удалось получить список акций с MOEX")

    all_tickers = [s["ticker"] for s in all_stocks]
    stock_map   = {s["ticker"]: s for s in all_stocks}

    today     = date.today()
    from_date = today.replace(year=today.year - years).isoformat()
    till_date = today.isoformat()

    # 2. Параллельная загрузка истории и дивидендов для всех бумаг
    histories_list, dividends_list = await asyncio.gather(
        asyncio.gather(*[fetch_price_history(t, from_date, till_date) for t in all_tickers]),
        asyncio.gather(*[fetch_dividends_data(t) for t in all_tickers]),
    )

    tickers_info = [
        {
            "ticker":    t,
            "name":      stock_map[t]["name"],
            "sector":    stock_map[t]["sector"],
            "market_cap": stock_map[t]["market_cap"],
            "history":   histories_list[i],
            "dividends": dividends_list[i],
        }
        for i, t in enumerate(all_tickers)
    ]

    result = build_dynamic_portfolio(tickers_info, min_cagr_pct=min_cagr)
    result["params"]["total_from_moex"] = len(all_stocks)
    return result


class PortfolioChartRequest(BaseModel):
    tickers:    list[str]    # тикеры из умного портфеля
    weights:    list[float]  # доли (0..1), сумма ≈ 1
    start_year: int
    amount:     float        # сумма одной закупки (₽) на весь портфель
    frequency:  str          # "once" | "monthly" | "weekly"


@app.post("/api/portfolio-chart")
async def portfolio_chart(body: PortfolioChartRequest) -> dict:
    """
    Строит временной ряд стоимости портфеля для Chart.js.
    Принимает динамические тикеры и веса из умного портфеля.
    """
    current_year = date.today().year
    if not (2010 <= body.start_year <= current_year):
        raise HTTPException(400, f"Год должен быть в диапазоне 2010–{current_year}")
    if body.amount < 100:
        raise HTTPException(400, "Минимальная сумма — 100 ₽")
    if body.frequency not in ("once", "monthly", "weekly"):
        raise HTTPException(400, "frequency: once | monthly | weekly")
    if not body.tickers or len(body.tickers) != len(body.weights):
        raise HTTPException(400, "Длины tickers и weights должны совпадать")

    tickers   = body.tickers
    from_date = f"{body.start_year}-01-01"
    till_date = date.today().isoformat()

    histories_list, dividends_list, prices_map = await asyncio.gather(
        asyncio.gather(*[fetch_price_history(t, from_date, till_date) for t in tickers]),
        asyncio.gather(*[fetch_dividends_data(t) for t in tickers]),
        fetch_prices(tickers),
    )
    histories = dict(zip(tickers, histories_list))
    dividends = dict(zip(tickers, dividends_list))

    ticker_results: dict[str, dict] = {}
    for ticker, weight in zip(tickers, body.weights):
        hist   = histories.get(ticker) or []
        divs   = dividends.get(ticker) or []
        cp     = prices_map.get(ticker, {}).get("price")  # type: ignore[union-attr]
        amount = body.amount * weight

        if not hist:
            ticker_results[ticker] = {"error": "Нет данных MOEX"}
            continue

        ticker_results[ticker] = run_dca(hist, amount, body.frequency, cp, divs)

    return build_chart_series(ticker_results, histories, body.start_year)


@app.get("/api/backtest/tickers")
async def backtest_tickers() -> dict:
    """Возвращает список тикеров с именами для DCA-калькулятора."""
    companies = _get_companies()
    return {
        "tickers": [
            {"ticker": t, "name": c["name"]}
            for t, c in companies.items()
        ]
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str) -> dict:
    """Возвращает сохранённую аналитику по session_id (живёт 24 ч)."""
    data = _session_get(session_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Сессия не найдена или истекла (данные хранятся 24 часа)",
        )
    return data
