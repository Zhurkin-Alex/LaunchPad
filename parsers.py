# parsers.py
from __future__ import annotations

import io
import re
import logging
from typing import Optional

import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)

# Все известные тикеры (2–5 символов, как на MOEX)
KNOWN_TICKERS: frozenset[str] = frozenset({
    "SBER", "GAZP", "LKOH", "GMKN", "YDEX", "MGNT", "MTSS",
    "ROSN", "TATN", "VTBR", "NVTK", "SNGS", "PHOR", "PLZL",
    "CHMF", "AFLT", "X5", "OZON", "TCSG", "MOEX",
})

# Паттерн: слово из 1–5 заглавных латинских букв + опциональная цифра
_TICKER_RE = re.compile(r'\b([A-Z]{1,5}[0-9]?)\b')

try:
    import easyocr as _easyocr_module
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False
    logger.warning("easyocr не установлен — OCR изображений недоступен")

_ocr_reader: Optional[object] = None


def _get_ocr_reader() -> object:
    """Ленивая инициализация EasyOCR (модели ~300 МБ, скачиваются один раз)."""
    global _ocr_reader
    if not _EASYOCR_AVAILABLE:
        raise RuntimeError(
            "easyocr не установлен. Выполните: pip install easyocr"
        )
    if _ocr_reader is None:
        logger.info("Инициализация EasyOCR (первый запуск может занять ~30 с)...")
        _ocr_reader = _easyocr_module.Reader(["ru", "en"], gpu=False, verbose=False)
    return _ocr_reader


def extract_text_from_pdf(file_bytes: bytes, max_pages: int = 20) -> str:
    """Извлекает текст из PDF, не более max_pages страниц."""
    parts: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:max_pages]:
                text = page.extract_text()
                if text:
                    parts.append(text)
    except Exception as exc:
        raise ValueError(f"Не удалось прочитать PDF: {exc}") from exc
    return "\n".join(parts)


def extract_text_from_image(
    file_bytes: bytes, max_megapixels: float = 2.0
) -> str:
    """Запускает OCR на изображении, предварительно ограничивая разрешение."""
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Не удалось открыть изображение: {exc}") from exc

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    width, height = image.size
    max_pixels = int(max_megapixels * 1_000_000)
    if width * height > max_pixels:
        scale = (max_pixels / (width * height)) ** 0.5
        image = image.resize(
            (int(width * scale), int(height * scale)), Image.LANCZOS
        )
        logger.info(
            "Изображение уменьшено до %dx%d для OCR", image.width, image.height
        )

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    reader = _get_ocr_reader()
    results: list[str] = reader.readtext(buf.read(), detail=0)  # type: ignore[attr-defined]
    return " ".join(results)


def extract_tickers(text: str) -> list[str]:
    """Ищет все известные тикеры в тексте (case-insensitive), без дублей."""
    upper = text.upper()
    seen: set[str] = set()
    result: list[str] = []
    for match in _TICKER_RE.findall(upper):
        if match in KNOWN_TICKERS and match not in seen:
            seen.add(match)
            result.append(match)
    return result
