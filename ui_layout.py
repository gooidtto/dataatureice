"""Canonical desktop search/result layout.

The active executable entry point (ui_bootstrap.SearchApp) owns its complete
layout. This compatibility module must never mutate a live window after
construction; doing so previously produced the reported left/right split.
"""
from __future__ import annotations


def organize_search_toolbar(app):
    """Compatibility hook; SearchApp lays out its toolbar directly."""
    return None


def _normalize_search_controls(app):
    """Compatibility hook; never rebuild or re-parent live widgets."""
    return None


def _manage_categories(app):
    """Legacy compatibility entry point."""
    return None


def apply(app):
    """No-op: ui_bootstrap is the single source of truth for geometry."""
    return None
