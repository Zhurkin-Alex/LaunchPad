# portfolio.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

# TOP_TICKERS и WEIGHTS были удалены:
# симулятор графика (/api/portfolio-chart) теперь принимает
# динамические тикеры и веса из умного портфеля (/api/smart-portfolio).

# ── Динамическая подборка: метрики и фильтрация ───────────────────────────────

def _compute_metrics(history: list[dict], dividends: list[dict]) -> dict | None:
    """
    Вычисляет реальные метрики доходности по данным MOEX.

    history   : [{date: YYYY-MM-DD, close: float}, ...] хронологически
    dividends : [{date: YYYY-MM-DD, value: float}, ...] дивиденды на акцию (₽)

    Возвращает None, если данных недостаточно (< 6 месяцев торгов).
    """
    if not history or len(history) < 60:   # ~3 месяца торгов минимум
        return None

    start_price = float(history[0]["close"])
    end_price   = float(history[-1]["close"])
    if start_price <= 0:
        return None

    d0 = datetime.strptime(history[0]["date"],  "%Y-%m-%d")
    d1 = datetime.strptime(history[-1]["date"], "%Y-%m-%d")
    actual_years = max((d1 - d0).days / 365.25, 0.1)

    # Дивиденды за период истории
    start_date = history[0]["date"]
    end_date   = history[-1]["date"]
    total_divs = sum(
        float(d["value"]) for d in dividends
        if start_date <= d["date"] <= end_date
    )

    # Доходность цены
    price_return = (end_price - start_price) / start_price
    price_cagr   = (end_price / start_price) ** (1.0 / actual_years) - 1.0

    # Суммарная доходность (цена + дивиденды, без реинвестирования)
    total_end    = end_price + total_divs
    total_return = (total_end - start_price) / start_price
    total_cagr   = (total_end / start_price) ** (1.0 / actual_years) - 1.0

    # Среднегодовая дивидендная доходность
    div_yield_annual = (total_divs / start_price) / actual_years

    return {
        "actual_years":     round(actual_years, 1),
        "start_price":      round(start_price, 2),
        "end_price":        round(end_price, 2),
        "total_divs":       round(total_divs, 2),
        "price_return_pct": round(price_return * 100, 1),
        "price_cagr_pct":   round(price_cagr * 100, 1),
        "total_return_pct": round(total_return * 100, 1),
        "total_cagr_pct":   round(total_cagr * 100, 1),
        "div_yield_pct":    round(div_yield_annual * 100, 1),
    }


def build_dynamic_portfolio(
    tickers_info: list[dict],    # [{ticker, name, sector, rationale, history, dividends}, ...]
    min_cagr_pct: float = 8.0,  # порог суммарного CAGR %/год
    max_per_sector: int = 2,
    max_total: int = 10,
) -> dict:
    """
    Динамически формирует сбалансированный портфель на основе реальных данных MOEX.

    Алгоритм:
    1. Считаем метрики для всех тикеров.
    2. Фильтруем: total_cagr_pct < min_cagr_pct → в "отсев".
    3. Сортируем прошедших по total_cagr_pct (лучшие → первые).
    4. Берём не более max_per_sector из каждого сектора, итого max_total.
    5. Веса — пропорционально total_cagr (лучшие получают бо́льшую долю).
    """
    passed:   list[dict] = []
    rejected: list[dict] = []
    no_data:  list[dict] = []

    for info in tickers_info:
        m = _compute_metrics(info.get("history", []), info.get("dividends", []))
        if m is None:
            no_data.append({"ticker": info["ticker"], "name": info.get("name", ""), "reason": "нет данных MOEX"})
            continue

        entry = {
            "ticker":    info["ticker"],
            "name":      info.get("name", info["ticker"]),
            "sector":    info.get("sector", "—"),
            "rationale": info.get("rationale", ""),
            "metrics":   m,
        }

        if m["total_cagr_pct"] < min_cagr_pct:
            rejected.append({**entry, "reason": f"CAGR {m['total_cagr_pct']}% < {min_cagr_pct}%/год"})
        else:
            passed.append(entry)

    # Сортируем по суммарному CAGR (убывание)
    passed.sort(key=lambda x: -x["metrics"]["total_cagr_pct"])

    # Выбираем с диверсификацией по секторам
    sector_count: dict[str, int] = {}
    selected:     list[dict]     = []
    sector_skipped: list[dict]   = []

    for item in passed:
        sector = item["sector"]
        cnt    = sector_count.get(sector, 0)
        if cnt >= max_per_sector:
            sector_skipped.append({**item, "reason": f"сектор «{sector}» уже занят (≥{max_per_sector})"})
            continue
        sector_count[sector] = cnt + 1
        selected.append(item)
        if len(selected) >= max_total:
            break

    # Веса: пропорционально total_cagr в процентах
    total_score = sum(i["metrics"]["total_cagr_pct"] for i in selected)
    for item in selected:
        item["weight"] = round(item["metrics"]["total_cagr_pct"] / total_score, 3) if total_score else 0

    return {
        "portfolio":     selected,
        "rejected":      rejected + sector_skipped,
        "no_data":       no_data,
        "params": {
            "min_cagr_pct":    min_cagr_pct,
            "max_per_sector":  max_per_sector,
            "max_total":       max_total,
            "total_analyzed":  len(tickers_info),
        },
    }


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _monthly_price_map(history: list[dict]) -> dict[str, float]:
    """Последняя цена закрытия за каждый месяц (итерация в хронологическом порядке)."""
    mp: dict[str, float] = {}
    for h in history:
        mp[h["date"][:7]] = float(h["close"])
    return mp


def _monthly_spending_map(purchases: list[dict]) -> dict[str, float]:
    """Сумма actual_spent по месяцам."""
    ms: dict[str, float] = defaultdict(float)
    for p in purchases:
        ms[p["date"][:7]] += p["actual_spent"]
    return dict(ms)


def _monthly_div_map(dividend_events: list[dict]) -> dict[str, float]:
    """Сумма дивидендов, начисленных за каждый месяц."""
    md: dict[str, float] = defaultdict(float)
    for ev in dividend_events:
        md[ev["date"][:7]] += ev["received"]
    return dict(md)


# ── Построение временного ряда для Chart.js ───────────────────────────────────

def build_chart_series(
    ticker_results: dict[str, dict],   # ticker → результат run_dca
    histories:      dict[str, list[dict]],  # ticker → история цен MOEX
    start_year:     int,
) -> dict:
    """
    Строит ежемесячный ряд стоимости портфеля.

    Для каждого месяца:
    - portfolio_value  = Σ(накопленные_акции × цена_конца_месяца) по всем тикерам
    - с дивидендами    = portfolio_value + накопленные_дивиденды

    Возвращает dict с ключами: labels, invested, value_no_div, value_with_div, summary.
    """
    start_month = f"{start_year}-01"
    all_months: set[str] = set()

    processed: dict[str, dict] = {}
    for ticker, result in ticker_results.items():
        if "error" in result:
            continue
        hist = histories.get(ticker) or []
        if not hist:
            continue

        mp = _monthly_price_map(hist)
        ms = _monthly_spending_map(result.get("purchases", []))
        md = _monthly_div_map(result.get("dividend_events", []))

        # month → последнее значение cumulative_shares в этом месяце
        month_to_shares: dict[str, int] = {}
        for p in result.get("purchases", []):
            month_to_shares[p["date"][:7]] = p["cumulative_shares"]

        all_months.update(mp.keys())
        processed[ticker] = {
            "monthly_prices":   mp,
            "monthly_spending": ms,
            "monthly_divs":     md,
            "month_to_shares":  month_to_shares,
        }

    if not processed:
        return {"error": "MOEX не вернул данные для построения графика"}

    labels = sorted(m for m in all_months if m >= start_month)
    if not labels:
        return {"error": "Нет исторических данных за указанный период"}

    last_shares: dict[str, int]   = {t: 0   for t in processed}
    last_price:  dict[str, float] = {t: 0.0 for t in processed}
    cum_invested = 0.0
    cum_divs     = 0.0

    invested_series:   list[float] = []
    value_no_div:      list[float] = []
    value_with_div:    list[float] = []

    for month in labels:
        month_invested = 0.0
        month_divs     = 0.0

        for ticker, td in processed.items():
            if month in td["month_to_shares"]:
                last_shares[ticker] = td["month_to_shares"][month]
            if month in td["monthly_prices"]:
                last_price[ticker] = td["monthly_prices"][month]

            month_invested += td["monthly_spending"].get(month, 0)
            month_divs     += td["monthly_divs"].get(month, 0)

        cum_invested += month_invested
        cum_divs     += month_divs

        portfolio_val = sum(last_shares[t] * last_price[t] for t in processed)

        invested_series.append(round(cum_invested))
        value_no_div.append(round(portfolio_val))
        value_with_div.append(round(portfolio_val + cum_divs))

    final_val     = value_no_div[-1]   if value_no_div   else 0
    final_val_div = value_with_div[-1] if value_with_div else 0
    total_inv     = invested_series[-1] if invested_series else 0
    pnl           = final_val - total_inv
    pnl_div       = final_val_div - total_inv

    return {
        "labels":         labels,
        "invested":       invested_series,
        "value_no_div":   value_no_div,
        "value_with_div": value_with_div,
        "summary": {
            "total_invested":       round(total_inv),
            "final_value":          round(final_val),
            "total_dividends":      round(cum_divs),
            "final_value_with_div": round(final_val_div),
            "pnl":                  round(pnl),
            "pnl_pct":              round(pnl / total_inv * 100, 1) if total_inv else None,
            "pnl_with_div":         round(pnl_div),
            "pnl_pct_with_div":     round(pnl_div / total_inv * 100, 1) if total_inv else None,
            "ticker_count":         len(processed),
        },
    }
