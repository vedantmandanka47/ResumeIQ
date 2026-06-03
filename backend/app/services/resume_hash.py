"""Stable hashing for resume content."""

import hashlib


def hash_resume_content(resume_content: str) -> str:
    normalized = "\n".join(line.rstrip() for line in resume_content.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
