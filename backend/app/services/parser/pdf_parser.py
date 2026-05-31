"""PDF resume text extraction."""

import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for index, page in enumerate(pdf.pages):
                try:
                    pages.append((page.extract_text(layout=True) or "").strip())
                except Exception as exc:
                    logger.warning("Failed to extract PDF page %s: %s", index, exc)

        text = "\n\n".join(page for page in pages if page).strip()
        if len(text) < 100:
            logger.warning(
                "PDF extraction returned only %s characters. Document may be image-based or encrypted.",
                len(text),
            )
        return text
    except Exception as exc:
        logger.error("PDF extraction failed entirely: %s", exc, exc_info=True)
        return ""
