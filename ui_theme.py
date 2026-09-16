"""Modern eye-care visual system with restrained colorful accents."""

THEME = {
    # Eye-care base: warm, low-glare surfaces instead of pure white everywhere.
    "window_bg": "#eef2ee",
    "surface": "#fbfcf8",
    "surface_alt": "#f3f6f1",
    "surface_subtle": "#e9efe9",
    "table_bg": "#fbfcf8",
    "table_header": "#e8eee8",
    "border": "#cbd5cc",
    "border_soft": "#dfe6df",
    "border_strong": "#aebbb0",

    # High-clarity text: selection never turns text gray or white.
    "text": "#18201b",
    "text_secondary": "#334139",
    "text_muted": "#68756d",

    # Modern blue-green primary accent.
    "accent": "#2878c8",
    "accent_hover": "#1f66ad",
    "accent_soft": "#e2effb",
    "selection": "#e5f0e8",
    "selection_strong": "#d5e8dc",
    "selection_text": "#18201b",

    "success": "#28734b",
    "warning": "#9a6818",
    "danger": "#a33f4a",

    # Subtle chromatic bands: used for visual rhythm, not for data meaning.
    # They stay light enough to preserve black text readability.
    "model_bands": (
        "#fbfcf8",
        "#f5f8ff",
        "#f5faf6",
        "#fff8f1",
        "#f8f4ff",
        "#f1f9fa",
    ),
    "period_separator": "#b8cfe5",
    "model_separator": "#b9d8c4",
    "separator_line": "#d7e0d8",
    "model_separator_line": "#c7d5cc",

    # Buttons: clean modern cards with restrained accent text.
    "button_bg": "#f9fbf8",
    "button_hover": "#edf4ee",
    "button_pressed": "#dfeae2",
    "button_border": "#c4d0c6",
    "button_text": "#18201b",
    "button_accent_text": "#1f66ad",
    "button_disabled": "#e1e6e2",

    # Layout rhythm.
    "space_xs": 3,
    "space_sm": 6,
    "space_md": 10,
    "space_lg": 14,
    "space_xl": 20,
    "button_pad_x": 11,
    "button_pad_y": 6,
    "primary_pad_x": 14,
    "primary_pad_y": 7,
    "table_row_height": 36,
    "table_header_height": 32,
    "result_gap": 3,
    "period_gap": 7,
    "model_gap": 12,
}

FONT_FAMILY = "SimHei"
FONT_BODY = (FONT_FAMILY, 10)
FONT_TABLE_DATA = (FONT_FAMILY, 10, "bold")
FONT_LABEL = (FONT_FAMILY, 11)
FONT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_SEARCH = (FONT_FAMILY, 14)
