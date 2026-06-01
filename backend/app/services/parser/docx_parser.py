"""DOCX resume text extraction."""

import io
import logging

from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        document = Document(io.BytesIO(file_bytes))
        blocks = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    blocks.append(" | ".join(cells))
        return "\n".join(blocks)
    except Exception as exc:
        logger.error("DOCX extraction failed: %s", exc, exc_info=True)
        return ""
