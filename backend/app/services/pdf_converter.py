"""DOCX to PDF conversion with automatic fallback."""

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class PdfConversionError(RuntimeError):
    """Raised when every PDF conversion strategy fails."""


def _convert_with_libreoffice(docx_path: Path, pdf_path: Path, timeout_seconds: int) -> None:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        raise PdfConversionError("LibreOffice executable was not found")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            executable,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(docx_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if result.returncode != 0:
        raise PdfConversionError(result.stderr.strip() or result.stdout.strip() or "LibreOffice conversion failed")

    generated = pdf_path.parent / f"{docx_path.stem}.pdf"
    if generated.exists() and generated != pdf_path:
        generated.replace(pdf_path)
    if not pdf_path.exists():
        raise PdfConversionError("LibreOffice did not create a PDF")


def _convert_with_docx2pdf(docx_path: Path, pdf_path: Path) -> None:
    from docx2pdf import convert

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    convert(str(docx_path), str(pdf_path))
    if not pdf_path.exists():
        raise PdfConversionError("docx2pdf did not create a PDF")


def convert_docx_to_pdf(docx_path: Path, pdf_path: Path, timeout_seconds: int = 60) -> tuple[Path | None, str | None]:
    errors: list[str] = []
    try:
        _convert_with_libreoffice(docx_path, pdf_path, timeout_seconds)
        return pdf_path, None
    except Exception as exc:
        logger.warning("LibreOffice PDF conversion failed for %s: %s", docx_path, exc)
        errors.append(f"LibreOffice: {exc}")

    try:
        _convert_with_docx2pdf(docx_path, pdf_path)
        return pdf_path, None
    except Exception as exc:
        logger.warning("docx2pdf conversion failed for %s: %s", docx_path, exc)
        errors.append(f"docx2pdf: {exc}")

    return None, "; ".join(errors)
