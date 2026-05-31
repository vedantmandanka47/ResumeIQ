"""Resume document parsers."""

from app.services.parser.docx_parser import extract_text_from_docx
from app.services.parser.pdf_parser import extract_text_from_pdf

__all__ = ["extract_text_from_pdf", "extract_text_from_docx"]
