# backtest.py
from __future__ import annotations

import bisect
from datetime import date
from typing import Optional


# ── Фильтры торговых дней по частоте ─────────────────────────────────────────

def _filter_monthly(history: list[dict]) -> list[dict]:
    """Первый торговый день каждого месяца."""
    seen: set[str] = set()
    result: list[dict] = []
    for h in history:
        month = h["date"][:7]  # "YYYY-MM"
        if month not in seen:
            seen.add(month)
            result.append(h)
    return result


def _filter_weekly(history: list[dict]) -> list[dict]:
    """Первый торговый день каждой ISO-недели."""
    seen: set[tuple] = set()
    result: list[dict] = []
    for h in history:
        d = date.fromisoformat(h["date"])
        week = d.isocalendar()[:2]  # (year, week_number)
        if week not in seen:
            seen.add(week)
            result.append(h)
    return result


# ── Основной расчёт ───────────────────────────────────────────────────────────

def _calc_dividends(
    purchases: list[dict],
    dividends: list[dict],
) -> tuple[float, list[dict]]:
    """
    Рассчитывает дивиденды, полученные в течение периода.

    Для каждой выплаты находит количество акций на дату закрытия реестра
    бинарным поиском по отсортированному списку покупок.

    Возвращает (total_dividends_rub, list_of_dividend_events).
    """
    if not purchases or not dividends:
        return 0.0, []

    purchase_dates = [p["date"] for p in purchases]
    cumulative     = [p["cumulative_shares"] for p in purchases]
    first_date     = purchase_dates[0]

    total = 0.0
    events: list[dict] = []

    for div in dividends:
        div_date  = div["date"]
        div_value = div["value"]

        # Дивиденд начислен раньше первой покупки — пропускаем
        if div_date < first_date:
            continue

        # bisect_right возвращает индекс первой записи > div_date
        # idx - 1 = последняя покупка до или в день дивиденда
        idx = bisect.bisect_right(purchase_dates, div_date) - 1
        if idx < 0:
            continue

        shares_held = cumulative[idx]
        received    = round(shares_held * div_value, 2)
        total       = round(total + received, 2)

        events.append({
            "date":            div_date,
            "value_per_share": div_value,
            "shares_held":     shares_held,
            "received":        received,
            "cumulative_div":  total,
        })

    return total, events


def run_dca(
    history: list[dict],
    amount: float,
    frequency: str,
    current_price: Optional[float],
    dividends: Optional[list[dict]] = None,
) -> dict:
    """
    Рассчитывает результат DCA-стратегии.

    history:       список {"date": "YYYY-MM-DD", "close": float}
    amount:        сумма одной закупки в рублях
    frequency:     "once" | "monthly" | "weekly"
    current_price: текущая цена с MOEX (для расчёта доходности)
    dividends:     список {"date": "YYYY-MM-DD", "value": float} из MOEX

    Возвращает dict с ключами purchases, summary, dividend_events.
    """
    if not history:
        return {"error": "Нет исторических данных MOEX для данного тикера и периода"}

    history_sorted = sorted(history, key=lambda x: x["date"])

    if frequency == "once":
        purchase_days = [history_sorted[0]]
    elif frequency == "monthly":
        purchase_days = _filter_monthly(history_sorted)
    elif frequency == "weekly":
        purchase_days = _filter_weekly(history_sorted)
    else:
        purchase_days = [history_sorted[0]]

    purchases: list[dict] = []
    total_shares = 0
    total_invested = 0.0

    for day in purchase_days:
        price = day["close"]
        if not price or price <= 0:
            continue

        shares = int(amount / price)
        if shares == 0:
            continue

        actual_spent = round(shares * price, 2)
        total_shares += shares
        total_invested = round(total_invested + actual_spent, 2)

        purchases.append({
            "date":              day["date"],
            "price":             round(price, 2),
            "shares_bought":     shares,
            "actual_spent":      actual_spent,
            "cumulative_shares": total_shares,
            "cumulative_invested": total_invested,
        })

    if not purchases:
        return {
            "error": (
                "Не удалось совершить ни одной покупки: "
                "выбранная сумма меньше стоимости одной акции в указанный период"
            )
        }

    # ── P&L без дивидендов ────────────────────────────────────────────────────
    current_value: Optional[float] = None
    pnl:           Optional[float] = None
    pnl_pct:       Optional[float] = None

    if current_price and current_price > 0:
        current_value = round(total_shares * current_price, 2)
        pnl           = round(current_value - total_invested, 2)
        pnl_pct       = round(pnl / total_invested * 100, 2) if total_invested > 0 else None

    avg_buy_price = round(total_invested / total_shares, 2) if total_shares > 0 else None

    # ── P&L с дивидендами ─────────────────────────────────────────────────────
    total_dividends, dividend_events = _calc_dividends(purchases, dividends or [])

    pnl_with_div:     Optional[float] = None
    pnl_pct_with_div: Optional[float] = None

    if pnl is not None:
        pnl_with_div     = round(pnl + total_dividends, 2)
        pnl_pct_with_div = (
            round(pnl_with_div / total_invested * 100, 2) if total_invested > 0 else None
        )

    return {
        "purchases":       purchases,
        "dividend_events": dividend_events,
        "summary": {
            "total_invested":      total_invested,
            "total_shares":        total_shares,
            "avg_buy_price":       avg_buy_price,
            "current_price":       current_price,
            "current_value":       current_value,
            # без дивидендов
            "pnl":                 pnl,
            "pnl_pct":             pnl_pct,
            # дивиденды
            "total_dividends":     total_dividends,
            "dividend_count":      len(dividend_events),
            # с дивидендами
            "pnl_with_div":        pnl_with_div,
            "pnl_pct_with_div":    pnl_pct_with_div,
            "purchase_count":      len(purchases),
            "first_purchase_date": purchases[0]["date"],
            "last_purchase_date":  purchases[-1]["date"],
        },
    }
