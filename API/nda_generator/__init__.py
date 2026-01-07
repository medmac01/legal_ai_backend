"""
NDA Generator module for generating Non-Disclosure Agreements.
Uses Jinja2 templates for initial generation and AI for modifications.
"""

from .rules_engine import build_llm_prompt
from .j2_engine import render_template, get_available_templates

# Import NDAService lazily to avoid potential circular imports
def get_nda_service():
    from .nda_service import NDAService
    return NDAService

__all__ = ["get_nda_service", "build_llm_prompt", "render_template", 
           "get_available_templates", "NDAService"]

# Lazy import for NDAService
def __getattr__(name):
    if name == "NDAService":
        from .nda_service import NDAService
        return NDAService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
