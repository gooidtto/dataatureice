"""Unified visual theme and shared UI safeguards for the desktop search app."""
import tkinter as _tk
import types as _types

THEME = {
    "window_bg": "#e8f1e7",
    "surface": "#f4f8f2",
    "surface_alt": "#eaf3e8",
    "surface_subtle": "#dfeadd",
    "table_bg": "#f7faf5",
    "table_header": "#d9e7d6",
    "border": "#b5c8b2",
    "border_soft": "#cad9c7",
    "text": "#18251b",
    "text_secondary": "#304536",
    "text_muted": "#5b6d5e",
    "accent": "#557b5b",
    "accent_hover": "#466b4d",
    "selection": "#d4e6d2",
    "selection_strong": "#c2dcc0",
    "success": "#4f7656",
    "warning": "#806b3d",
    "danger": "#875858",
    "model_bands": ("#eff6ed", "#edf4eb", "#f1f6ef", "#eaf2e8", "#f3f7f1"),
    "period_separator": "#9bbfc0",
    "model_separator": "#c9a77a",
    "button_bg": "#e6f0e4",
    "button_hover": "#d9e8d7",
    "button_pressed": "#c9ddc7",
    "button_border": "#aec3aa",
    "button_text": "#203226",
    "button_accent_text": "#3f6847",
    "button_disabled": "#cfdacf",
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

_OriginalFrame = _tk.Frame

class _SeparatorAwareFrame(_OriginalFrame):
    def __init__(self, master=None, **kwargs):
        height = kwargs.get("height")
        if kwargs.get("highlightthickness") == 1:
            if height == THEME["period_gap"]:
                kwargs["background"] = THEME["period_separator"]
                kwargs["highlightbackground"] = THEME["period_separator"]
            elif height == THEME["model_gap"]:
                kwargs["background"] = THEME["model_separator"]
                kwargs["highlightbackground"] = THEME["model_separator"]
        super().__init__(master, **kwargs)

_tk.Frame = _SeparatorAwareFrame

FONT_FAMILY = "SimHei"
FONT_BODY = (FONT_FAMILY, 10)
FONT_LABEL = (FONT_FAMILY, 11)
FONT_TITLE = (FONT_FAMILY, 11, "bold")
FONT_SEARCH = (FONT_FAMILY, 14)

# The legacy App initializer patches the app_actions module after the UI has
# been created. That patch replaced the working Toplevel history popup with a
# child-frame implementation that is clipped by the search-bar container.
# Keep the original module API, but protect the four history hooks and add the
# missing clear action to the existing Toplevel implementation.
try:
    import app_actions as _history_actions
    _legacy_refresh = _history_actions._refresh_suggestions
    _legacy_hide = _history_actions._hide_suggestions
    _legacy_show = _history_actions._show_suggestions
    _legacy_dismiss = _history_actions._dismiss_suggestions

    def _refresh_history(app):
        _legacy_refresh(app)
        popup = getattr(app, "suggest_popup", None)
        if popup is None:
            return
        try:
            if not popup.winfo_exists():
                return
            clear_button = getattr(app, "_history_clear_button", None)
            if clear_button is not None and clear_button.winfo_exists():
                clear_button.destroy()
            clear_button = _tk.Button(
                popup,
                text="清除",
                command=getattr(app, "clear_search_history", lambda: None),
                bg=THEME["surface_alt"],
                fg=THEME["text_secondary"],
                activebackground=THEME["selection"],
                activeforeground=THEME["text"],
                relief="flat",
                bd=0,
                font=FONT_BODY,
                cursor="hand2",
            )
            clear_button.place(relx=1.0, x=-6, y=4, anchor="ne")
            app._history_clear_button = clear_button
            popup.configure(bg=THEME["surface_alt"])
        except _tk.TclError:
            pass

    _history_actions._refresh_suggestions = _refresh_history
    _history_actions._hide_suggestions = _legacy_hide
    _history_actions._show_suggestions = _refresh_history
    _history_actions._dismiss_suggestions = _legacy_dismiss

    class _ProtectedActionsModule(_types.ModuleType):
        _protected_history_hooks = frozenset({
            "_refresh_suggestions", "_hide_suggestions",
            "_show_suggestions", "_dismiss_suggestions",
        })
        def __setattr__(self, name, value):
            if name in self._protected_history_hooks and name in self.__dict__:
                return
            super().__setattr__(name, value)

    if not isinstance(_history_actions, _ProtectedActionsModule):
        _history_actions.__class__ = _ProtectedActionsModule
except Exception:
    pass
