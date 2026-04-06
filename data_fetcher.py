# data_fetcher.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MOEX_ISS = "https://iss.moex.com/iss"
BOARD = "TQBR"  # основной режим торгов акциями на MOEX

# Справочник секторов российских акций (MOEX не возвращает SECTORID)
TICKER_SECTOR: dict[str, str] = {
    # Нефтегаз
    "ROSN": "Нефтегаз", "LKOH": "Нефтегаз", "GAZP": "Нефтегаз", "NVTK": "Нефтегаз",
    "TATN": "Нефтегаз", "TATNP": "Нефтегаз", "SIBN": "Нефтегаз", "SNGS": "Нефтегаз",
    "SNGSP": "Нефтегаз", "BANE": "Нефтегаз", "BANEP": "Нефтегаз", "RNFT": "Нефтегаз",
    # Финансы
    "SBER": "Финансы", "SBERP": "Финансы", "VTBR": "Финансы", "TCSG": "Финансы",
    "MOEX": "Финансы", "CBOM": "Финансы", "SFIN": "Финансы", "AFKS": "Финансы",
    "BSPB": "Финансы", "RENI": "Финансы", "MBNK": "Финансы", "SPBE": "Финансы",
    # Металлургия
    "GMKN": "Металлургия", "NLMK": "Металлургия", "CHMF": "Металлургия",
    "MAGN": "Металлургия", "ALRS": "Металлургия", "RUAL": "Металлургия",
    "MTLR": "Металлургия", "MTLRP": "Металлургия", "ENPG": "Металлургия",
    "RASP": "Металлургия", "VSMO": "Металлургия", "KZOS": "Металлургия",
    # Золото / драгметаллы
    "PLZL": "Золото", "UGLD": "Золото", "SELG": "Золото",
    # Химия / удобрения
    "PHOR": "Химия", "AKRN": "Химия", "KAZT": "Химия", "NKNC": "Химия",
    "NKNCP": "Химия", "KROT": "Химия",
    # Ритейл
    "MGNT": "Ритейл", "X5": "Ритейл", "OZON": "Ритейл", "LENT": "Ритейл",
    "FIXP": "Ритейл", "DSKY": "Ритейл",
    # Технологии / IT
    "YDEX": "Технологии", "VKCO": "Технологии", "POSI": "Технологии",
    "ASTR": "Технологии", "HEAD": "Технологии", "CIAN": "Технологии",
    "HHRU": "Технологии", "DIAS": "Технологии", "PRMD": "Технологии",
    # Телеком
    "MTSS": "Телеком", "RTKM": "Телеком", "RTKMP": "Телеком",
    "TTLK": "Телеком", "MGTSP": "Телеком",
    # Электроэнергетика
    "HYDR": "Энергетика", "IRAO": "Энергетика", "FEES": "Энергетика",
    "UPRO": "Энергетика", "OGKB": "Энергетика", "MSNG": "Энергетика",
    "TGKB": "Энергетика", "DVEC": "Энергетика", "TGKBP": "Энергетика",
    "MRKP": "Энергетика", "MRKV": "Энергетика", "MRKU": "Энергетика",
    "MRKC": "Энергетика", "MRKZ": "Энергетика",
    # Транспорт
    "FLOT": "Транспорт", "AFLT": "Транспорт", "NMTP": "Транспорт",
    "FESH": "Транспорт", "GLTR": "Транспорт", "GTRK": "Транспорт",
    # Строительство / недвижимость
    "SMLT": "Строительство", "PIKK": "Строительство", "LSRG": "Строительство",
    "ETLN": "Строительство", "LSNGP": "Строительство",
    # АПК / пищевая
    "AQUA": "АПК", "GCHE": "АПК", "AGRO": "АПК",
    "BELU": "Потреб. товары", "ABRD": "Потреб. товары",
    # Промышленность
    "UNAC": "Промышленность", "UWGN": "Промышленность", "AMEZ": "Промышленность",
    "KCHE": "Промышленность",
    # Здравоохранение
    "ABIO": "Здравоохранение",
    # Финансы (дополнительно)
    "T": "Финансы", "SVCB": "Финансы", "DOMRF": "Финансы", "LEAS": "Финансы",
    # Нефтегаз / транспортировка
    "TRNFP": "Нефтегаз", "TRNF": "Нефтегаз", "EUTR": "Транспорт",
    # Металлургия (дополнительно)
    "TRMK": "Металлургия", "KMAZ": "Промышленность", "SVAV": "Промышленность",
    # Строительство (дополнительно)
    "SGZH": "Строительство", "GLRX": "Строительство",
    # Энергетика (дополнительно)
    "MSRS": "Энергетика", "TGKA": "Энергетика", "TGKN": "Энергетика", "ELFV": "Энергетика",
    # Ритейл (дополнительно)
    "FIXR": "Ритейл", "MVID": "Ритейл", "HNFG": "Ритейл", "VSEH": "Ритейл",
    # АПК / пищевая (дополнительно)
    "RAGR": "АПК",
    # Здравоохранение (дополнительно)
    "MDMG": "Здравоохранение", "GEMC": "Здравоохранение", "OZPH": "Здравоохранение",
    "APTK": "Здравоохранение",
    # Технологии (дополнительно)
    "CNRU": "Технологии", "SOFL": "Технологии", "DATA": "Технологии",
    "BAZA": "Технологии", "IVAT": "Технологии",
    # Каршеринг / мобильность
    "DELI": "Транспорт", "WUSH": "Транспорт",
    # Другое
    "RKKE": "Добыча", "ALNU": "Промышленность",
}

# ── Простой TTL-кэш в памяти ──────────────────────────────────────────────────
_cache: dict[str, tuple[float, object]] = {}
_PRICE_TTL  = 3_600    # цены: 1 час
_DIV_TTL    = 86_400   # история дивидендов: 24 часа
_HIST_TTL   = 86_400   # исторические данные: 24 часа
_STOCKS_TTL = 3_600    # список акций MOEX: 1 час


def _get(key: str, ttl: float) -> Optional[object]:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < ttl:
        return entry[1]
    return None


def _set(key: str, value: object) -> None:
    _cache[key] = (time.time(), value)


# ── MOEX: текущие цены ────────────────────────────────────────────────────────

async def fetch_prices(tickers: list[str]) -> dict[str, dict]:
    """
    Возвращает {TICKER: {price, price_date, currency}} для переданных тикеров.
    Использует LAST (если торги идут) или PREVPRICE (предыдущее закрытие).
    При ошибке — возвращает пустой dict, аналитика не падает.
    """
    if not tickers:
        return {}

    cache_key = "prices:" + ",".join(sorted(tickers))
    cached = _get(cache_key, _PRICE_TTL)
    if cached is not None:
        return cached  # type: ignore[return-value]

    url = f"{MOEX_ISS}/engines/stock/markets/shares/boards/{BOARD}/securities.json"
    params = {
        "securities": ",".join(tickers),
        "iss.meta": "off",
        "iss.only": "securities,marketdata",
        "securities.columns": "SECID,PREVPRICE,PREVDATE,CURRENCYID",
        "marketdata.columns": "SECID,LAST",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        logger.warning("MOEX price fetch failed: %s", exc)
        return {}

    sec_cols: list[str] = raw["securities"]["columns"]
    sec_rows: list[list]  = raw["securities"]["data"]
    md_cols:  list[str] = raw["marketdata"]["columns"]
    md_rows:  list[list]  = raw["marketdata"]["data"]

    def idx(cols: list[str], name: str) -> int:
        return cols.index(name)

    sec_by_ticker = {r[idx(sec_cols, "SECID")]: r for r in sec_rows}
    md_by_ticker  = {r[idx(md_cols,  "SECID")]: r for r in md_rows}

    result: dict[str, dict] = {}
    for ticker in tickers:
        sec = sec_by_ticker.get(ticker)
        if not sec:
            continue
        md = md_by_ticker.get(ticker)

        live_price: Optional[float] = None
        if md:
            lp = md[idx(md_cols, "LAST")]
            if lp:
                live_price = float(lp)

        prev_price = sec[idx(sec_cols, "PREVPRICE")]
        price = live_price if live_price is not None else (
            float(prev_price) if prev_price is not None else None
        )
        result[ticker] = {
            "price":      price,
            "price_date": sec[idx(sec_cols, "PREVDATE")] or "",
            "currency":   sec[idx(sec_cols, "CURRENCYID")] or "RUB",
            "is_live":    live_price is not None,
        }

    _set(cache_key, result)
    return result


# ── MOEX: история дивидендов ──────────────────────────────────────────────────

async def fetch_dividend_years(ticker: str) -> Optional[int]:
    """
    Возвращает количество уникальных годов, в которых были выплаты дивидендов.
    None — если запрос провалился (используется статическое значение).
    """
    cache_key = f"div:{ticker}"
    cached = _get(cache_key, _DIV_TTL)
    if cached is not None:
        return cached  # type: ignore[return-value]

    url = f"{MOEX_ISS}/securities/{ticker}/dividends.json"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params={"iss.meta": "off"})
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        logger.warning("MOEX dividends fetch failed for %s: %s", ticker, exc)
        return None

    cols: list[str] = raw.get("dividends", {}).get("columns", [])
    rows: list[list] = raw.get("dividends", {}).get("data", [])

    if not rows or "registryclosedate" not in cols:
        _set(cache_key, 0)
        return 0

    date_idx = cols.index("registryclosedate")
    years = {row[date_idx][:4] for row in rows if row[date_idx]}
    count = len(years)
    _set(cache_key, count)
    return count


# ── MOEX: полная история дивидендов с суммами (для DCA) ──────────────────────

async def fetch_dividends_data(ticker: str) -> list[dict]:
    """
    Возвращает историю дивидендных выплат:
    [{"date": "YYYY-MM-DD", "value": float}], только рублёвые выплаты, по дате.
    """
    cache_key = f"div_full:{ticker}"
    cached = _get(cache_key, _DIV_TTL)
    if cached is not None:
        return cached  # type: ignore[return-value]

    url = f"{MOEX_ISS}/securities/{ticker}/dividends.json"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params={"iss.meta": "off"})
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        logger.warning("MOEX dividends_data fetch failed for %s: %s", ticker, exc)
        _set(cache_key, [])
        return []

    cols: list[str] = raw.get("dividends", {}).get("columns", [])
    rows: list[list] = raw.get("dividends", {}).get("data", [])

    if not rows or "registryclosedate" not in cols or "value" not in cols:
        _set(cache_key, [])
        return []

    date_idx     = cols.index("registryclosedate")
    value_idx    = cols.index("value")
    currency_idx = cols.index("currencyid") if "currencyid" in cols else None

    result: list[dict] = []
    for row in rows:
        if currency_idx is not None and row[currency_idx] not in ("RUB", None):
            continue
        dt  = row[date_idx]
        val = row[value_idx]
        if dt and val and float(val) > 0:
            result.append({"date": dt, "value": float(val)})

    result.sort(key=lambda x: x["date"])
    _set(cache_key, result)
    return result


# ── Публичный интерфейс ───────────────────────────────────────────────────────

async def enrich_tickers(tickers: list[str]) -> dict[str, dict]:
    """
    Параллельно запрашивает MOEX для переданного списка тикеров.
    Возвращает {ticker: {price, price_date, currency, is_live, dividend_years_live}}.
    Никогда не бросает исключение — при ошибках просто возвращает пустые поля.
    """
    prices_result, div_results = await asyncio.gather(
        fetch_prices(tickers),
        asyncio.gather(
            *[fetch_dividend_years(t) for t in tickers],
            return_exceptions=True,
        ),
    )

    if isinstance(prices_result, Exception):
        prices_result = {}

    combined: dict[str, dict] = {}
    for ticker, div_res in zip(tickers, div_results):
        entry: dict = dict(prices_result.get(ticker, {}))  # type: ignore[arg-type]
        if isinstance(div_res, int):
            entry["dividend_years_live"] = div_res
        combined[ticker] = entry

    return combined


# ── MOEX: полный список акций биржи ──────────────────────────────────────────

async def fetch_moex_all_stocks(
    max_list_level: int = 2,
    max_count: int = 100,
) -> list[dict]:
    """
    Возвращает список всех акций с MOEX TQBR (уровень листинга ≤ max_list_level),
    отсортированных по капитализации по убыванию, не более max_count штук.
    Каждый элемент: {ticker, name, sector, list_level, market_cap}.
    """
    cache_key = f"stocks:{max_list_level}:{max_count}"
    cached = _get(cache_key, _STOCKS_TTL)
    if cached is not None:
        return cached  # type: ignore[return-value]

    url = f"{MOEX_ISS}/engines/stock/markets/shares/boards/{BOARD}/securities.json"
    params = {
        "iss.meta":           "off",
        "iss.only":           "securities,marketdata",
        "securities.columns": "SECID,SHORTNAME,SECTORID,LISTLEVEL",
        "marketdata.columns": "SECID,ISSUECAPITALIZATION",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        logger.warning("MOEX all stocks fetch failed: %s", exc)
        return []

    sec_cols = raw["securities"]["columns"]
    sec_data = raw["securities"]["data"]
    md_cols  = raw["marketdata"]["columns"]
    md_data  = raw["marketdata"]["data"]

    secs: dict[str, dict] = {}
    for row in sec_data:
        d = dict(zip(sec_cols, row))
        lvl = d.get("LISTLEVEL")
        if lvl is None or int(lvl) > max_list_level:
            continue
        ticker = d["SECID"]
        secs[ticker] = {
            "ticker":     ticker,
            "name":       d.get("SHORTNAME") or ticker,
            "sector":     TICKER_SECTOR.get(ticker, "—"),
            "list_level": int(lvl),
            "market_cap": 0.0,
        }

    for row in md_data:
        d = dict(zip(md_cols, row))
        ticker = d.get("SECID")
        if ticker in secs:
            cap = d.get("ISSUECAPITALIZATION")
            secs[ticker]["market_cap"] = float(cap) if cap else 0.0

    result = sorted(secs.values(), key=lambda x: -x["market_cap"])[:max_count]
    _set(cache_key, result)
    return result


# ── MOEX: исторические цены (для DCA-калькулятора) ────────────────────────────

async def fetch_price_history(
    ticker: str,
    from_date: str,
    till_date: str,
) -> list[dict]:
    """
    Возвращает список {"date": "YYYY-MM-DD", "close": float} для заданного периода.
    Использует постраничную загрузку MOEX ISS (100 записей/страница).
    Результат кэшируется на 24 ч (прошлые цены не меняются).
    """
    cache_key = f"hist:{ticker}:{from_date}:{till_date}"
    cached = _get(cache_key, _HIST_TTL)
    if cached is not None:
        return cached  # type: ignore[return-value]

    url = (
        f"{MOEX_ISS}/history/engines/stock/markets/shares"
        f"/boards/{BOARD}/securities/{ticker}.json"
    )
    base_params = {
        "from":                from_date,
        "till":                till_date,
        "iss.meta":            "off",
        "iss.only":            "history,history.cursor",
        "history.columns":     "TRADEDATE,CLOSE,VOLUME",
    }

    all_rows: list[dict] = []
    start = 0

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            while True:
                params = {**base_params, "start": start}
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                raw = resp.json()

                cols: list[str] = raw["history"]["columns"]
                rows: list[list] = raw["history"]["data"]

                if not rows:
                    break

                date_idx  = cols.index("TRADEDATE")
                close_idx = cols.index("CLOSE")

                for row in rows:
                    close = row[close_idx]
                    if close is not None and float(close) > 0:
                        all_rows.append({
                            "date":  row[date_idx],
                            "close": float(close),
                        })

                # Пагинация через cursor
                cursor_section = raw.get("history.cursor", {})
                cursor_rows    = cursor_section.get("data", [])
                cursor_cols    = cursor_section.get("columns", [])

                if not cursor_rows:
                    break

                idx_i      = cursor_cols.index("INDEX")
                idx_total  = cursor_cols.index("TOTAL")
                idx_pgsize = cursor_cols.index("PAGESIZE")

                cur_index    = cursor_rows[0][idx_i]
                cur_total    = cursor_rows[0][idx_total]
                cur_pagesize = cursor_rows[0][idx_pgsize]

                if cur_index + cur_pagesize >= cur_total:
                    break
                start = cur_index + cur_pagesize

    except Exception as exc:
        logger.warning("MOEX history fetch failed for %s: %s", ticker, exc)
        return []

    _set(cache_key, all_rows)
    return all_rows
