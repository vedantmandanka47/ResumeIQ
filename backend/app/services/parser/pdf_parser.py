"""PDF resume text extraction."""

import io
import logging
import re

import pdfplumber

logger = logging.getLogger(__name__)

_COMMON_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "projects",
    "education",
    "skills",
    "technical skills",
    "certifications",
    "awards",
    "achievements",
    "publications",
    "leadership",
}


def _looks_like_heading(line: str) -> bool:
    normalized = line.rstrip(":").strip().lower()
    if normalized in _COMMON_HEADINGS:
        return True
    return len(line) <= 48 and line.isupper() and any(char.isalpha() for char in line)


def _annotate_text(text: str) -> str:
    annotated: list[str] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            if annotated and annotated[-1]:
                annotated.append("")
            continue
        if _looks_like_heading(line):
            annotated.append(f"## {line.rstrip(':')}")
        elif re.match(r"^(?:[•*]|[-–]\s+)", line):
            annotated.append(f"- {line.lstrip('•*-– ').strip()}")
        else:
            annotated.append(line)
    return "\n".join(annotated).strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for index, page in enumerate(pdf.pages):
                try:
                    pages.append((page.extract_text(layout=True) or "").strip())
                except Exception as exc:
                    logger.warning("Failed to extract PDF page %s: %s", index, exc)

        text = _annotate_text("\n\n".join(page for page in pages if page).strip())
        if len(text) < 100:
            logger.warning(
                "PDF extraction returned only %s characters. Document may be image-based or encrypted.",
                len(text),
            )
        return text
    except Exception as exc:
        logger.error("PDF extraction failed entirely: %s", exc, exc_info=True)
        return ""
