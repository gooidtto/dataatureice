#!/usr/bin/env python3
"""Run the legacy 2026-07 materializer after removing its accidental heredoc marker."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'tools' / 'materialize_2026_07.py'
text = source.read_text(encoding='utf-8')
stripped = text.rstrip()
if stripped.endswith('\nPY'):
    stripped = stripped[:-3].rstrip() + '\n'
exec(compile(stripped, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
