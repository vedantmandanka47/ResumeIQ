"""Stable hashing for resume content."""

import hashlib


def hash_resume_content(
    resume_content: str,
    job_description: str | None = None,
    rewrite_instructions: str | None = None,
) -> str:
    """
    Stable SHA-256 hash over all three inputs that affect structured output.
    Any change to job_description or rewrite_instructions must produce a
    different hash so the cache never serves a stale result.
    """
    normalized = "\n".join(line.rstrip() for line in resume_content.strip().splitlines())
    jd_part = (job_description or "").strip()
    ri_part = (rewrite_instructions or "").strip()
    combined = f"{normalized}\x00{jd_part}\x00{ri_part}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
