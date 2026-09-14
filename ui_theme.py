"""Unified visual theme for the data-search desktop UI.

The palette is intentionally restrained: search is presentation-first, while
favorites carries the stronger interaction/selection emphasis.
"""

THEME = {
    # Window / surfaces
    "window_bg": "#f4f6f8",
    "surface": "#ffffff",
    "surface_alt": "#f8fafc",
    "surface_subtle": "#eef2f5",
    "table_bg": "#ffffff",
    "table_header": "#e9eef3",
    # Lines / typography
    "border": "#d7dee5",
    "border_soft": "#e5eaf0",
    "text": "#26323d",
    "text_secondary": "#596774",
    "text_muted": "#82909d",
    # Brand / interaction
    "accent": "#3f6f8f",
    "accent_hover": "#345f7c",
    "selection": "#dcecf6",
    "selection_strong": "#c9e1ef",
    # Semantic states
    "success": "#4f7f68",
    "warning": "#9a7740",
    "danger": "#a65d5d",
    # Search model grouping: deliberately low saturation
    "model_bands": ("#f3f7fa", "#f6f3f9", "#f2f7f4", "#faf7f0", "#f4f5f6"),
}

FONT_FAMILY = "微软雅黑"
FONT_BODY = (FONT_FAMILY, 10)
FONT_LABEL = (FONT_FAMILY, 11)
FONT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_SEARCH = (FONT_FAMILY, 14)
