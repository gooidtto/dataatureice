"""Unified visual theme for the data-search desktop UI.

The palette prioritizes legibility: light surfaces, dark text, restrained
accent colors, and stronger contrast for interactive controls.
"""

THEME = {
    "window_bg": "#eef1f4",
    "surface": "#ffffff",
    "surface_alt": "#f6f7f9",
    "surface_subtle": "#e9edf1",
    "table_bg": "#ffffff",
    "table_header": "#dfe4e9",
    "border": "#aeb8c2",
    "border_soft": "#d2d8de",
    "text": "#111820",
    "text_secondary": "#26333f",
    "text_muted": "#52616d",
    "accent": "#245f8a",
    "accent_hover": "#174d74",
    "selection": "#cfe4f3",
    "selection_strong": "#b9d8ec",
    "success": "#276749",
    "warning": "#8a5a00",
    "danger": "#a52a2a",
    "model_bands": ("#f1f6fa", "#f5f1f8", "#f0f7f3", "#f8f5ed", "#f1f3f5"),
    "space_xs": 3,
    "space_sm": 6,
    "space_md": 10,
    "space_lg": 14,
    "space_xl": 18,
    "button_pad_x": 10,
    "button_pad_y": 5,
    "primary_pad_x": 13,
    "primary_pad_y": 6,
    "table_row_height": 34,
    "table_header_height": 30,
    "result_gap": 2,
    "period_gap": 5,
    "model_gap": 10,
}

# Windows Tk installations reliably provide SimHei (黑体); use it consistently
# for visible UI text so labels, buttons, headings, and tables share one glyph
# system and remain visually crisp.
FONT_FAMILY = "SimHei"
FONT_BODY = (FONT_FAMILY, 10)
FONT_LABEL = (FONT_FAMILY, 11)
FONT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_SEARCH = (FONT_FAMILY, 14)
