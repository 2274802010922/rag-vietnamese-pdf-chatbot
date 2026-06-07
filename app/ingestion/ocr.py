from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OcrResult:
    text: str
    engine: str = "tesseract"


def is_tesseract_available() -> bool:
    """Return True when pytesseract and the Tesseract executable are available."""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except Exception:
        return False
    return True


def get_ocr_status() -> dict[str, Any]:
    """Return diagnostic information for OCR setup."""
    executable = shutil.which("tesseract")
    package_available = True
    version = None
    error = None
    try:
        import pytesseract

        if executable:
            version = str(pytesseract.get_tesseract_version())
    except Exception as exc:
        package_available = False
        error = str(exc)

    return {
        "engine": "tesseract",
        "available": bool(executable and package_available),
        "executable": executable,
        "python_package_available": package_available,
        "version": version,
        "error": error,
        "install_hint": "Cài Tesseract OCR và language pack vie, sau đó cài pytesseract/Pillow.",
    }


def extract_page_with_ocr(page: Any, language: str = "vie+eng", zoom: float = 2.0) -> OcrResult:
    """Render a PyMuPDF page and extract text using local Tesseract OCR."""
    import fitz
    import pytesseract
    from PIL import Image

    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(image, lang=language)
    logger.info("OCR extracted %s characters from page", len(text))
    return OcrResult(text=text)
