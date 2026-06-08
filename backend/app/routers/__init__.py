"""
ResumeIQ — routers package init.
Registers all routers in one place so main.py stays clean.
"""

from . import generation, health, resume

__all__ = ["generation", "health", "resume"]
