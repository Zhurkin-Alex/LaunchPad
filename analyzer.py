# analyzer.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent / "companies.json"
_COMPANIES: Optional[dict[str, dict]] = None

_RISK_COLORS: dict[str, str] = {
    "high": "danger",
    "medium": "warning",
    "low": "success",
}
_RISK_LABELS: dict[str, str] = {
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
}
_RISK_SCORES: dict[str, int] = {"high": 3, "medium": 2, "low": 1}
_NEWS_EMOJI: dict[str, str] = {
    "positive": "🟢",
    "neutral": "🟡",
    "negative": "🔴",
}


def _load_companies() -> dict[str, dict]:
    with open(_DB_PATH, encoding="utf-8") as fh:
        data: list[dict] = json.load(fh)
    return {item["ticker"]: item for item in data}


def _get_companies() -> dict[str, dict]:
    global _COMPANIES
    if _COMPANIES is None:
        _COMPANIES = _load_companies()
    return _COMPANIES


def analyze_ticker(ticker: str) -> dict:
    """Возвращает аналитику по одному тикеру или заглушку «неизвестно»."""
    ticker = ticker.strip().upper()
    company = _get_companies().get(ticker)

    if not company:
        return {
            "ticker": ticker,
            "company": "Неизвестно",
            "sector": "—",
            "geo_risk": "unknown",
            "geo_risk_color": "secondary",
            "geo_risk_label": "—",
            "key_risk": "—",
            "debt_ebitda": "—",
            "roe": "—",
            "sector_roe": "—",
            "roe_vs_sector": "—",
            "roe_color": "secondary",
            "dividend_years": "—",
            "free_float": "—",
            "news_sentiment": "❓",
            "found": False,
        }

    risk = company.get("geo_risk", "unknown")
    roe = float(company.get("roe", 0))
    sector_roe = float(company.get("sector_avg_roe", 0))
    roe_diff = roe - sector_roe
    roe_vs_sector = (
        f"+{roe_diff:.1f}%" if roe_diff >= 0 else f"{roe_diff:.1f}%"
    )

    return {
        "ticker": ticker,
        "company": company.get("name", ""),
        "sector": company.get("sector", ""),
        "geo_risk": risk,
        "geo_risk_color": _RISK_COLORS.get(risk, "secondary"),
        "geo_risk_label": _RISK_LABELS.get(risk, "—"),
        "key_risk": company.get("key_risk", "—"),
        "debt_ebitda": f"{float(company.get('debt_ebitda', 0)):.1f}x",
        "roe": f"{roe:.1f}%",
        "sector_roe": f"{sector_roe:.1f}%",
        "roe_vs_sector": roe_vs_sector,
        "roe_color": "success" if roe_diff >= 0 else "danger",
        "dividend_years": str(company.get("dividend_years", 0)),
        "free_float": f"{float(company.get('free_float', 0)):.0f}%",
        "news_sentiment": _NEWS_EMOJI.get(
            company.get("news_sentiment", "neutral"), "🟡"
        ),
        "found": True,
    }


def analyze_portfolio(tickers: list[str]) -> dict:
    """Анализирует список тикеров и возвращает построчную и сводную аналитику."""
    results = [analyze_ticker(t) for t in tickers]
    found = [r for r in results if r["found"]]

    if found:
        avg_score = (
            sum(_RISK_SCORES.get(r["geo_risk"], 0) for r in found) / len(found)
        )
        if avg_score >= 2.5:
            avg_risk, avg_risk_color = "Высокий", "danger"
        elif avg_score >= 1.5:
            avg_risk, avg_risk_color = "Средний", "warning"
        else:
            avg_risk, avg_risk_color = "Низкий", "success"

        high_debt_count = sum(
            1
            for r in found
            if r["debt_ebitda"] != "—"
            and float(r["debt_ebitda"].replace("x", "")) > 3.0
        )

        riskiest = max(
            found,
            key=lambda r: _RISK_SCORES.get(r["geo_risk"], 0),
        )
        riskiest_ticker = riskiest["ticker"]
    else:
        avg_risk, avg_risk_color = "—", "secondary"
        high_debt_count = 0
        riskiest_ticker = "—"

    return {
        "results": results,
        "portfolio": {
            "total_count": len(tickers),
            "found_count": len(found),
            "avg_risk": avg_risk,
            "avg_risk_color": avg_risk_color,
            "high_debt_count": high_debt_count,
            "riskiest": riskiest_ticker,
        },
    }
