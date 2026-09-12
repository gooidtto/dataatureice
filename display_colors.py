"""Shared model-group colors for search and favorites.

Each real-world model gets one distinct light color. Dates belonging to the
same model intentionally keep the same color. The palette avoids pure black
and white and provides strong visual separation between adjacent groups.
"""

MODEL_GROUP_COLORS = (
    "#DCEBFF",  # blue
    "#DFF4D8",  # green
    "#FFE4C2",  # orange
    "#E8DDF8",  # violet
    "#D8F1F1",  # cyan
    "#FFDDE6",  # pink
    "#FFF0B8",  # yellow
    "#DDE2F7",  # indigo
    "#D8F0E5",  # mint
    "#F8D9C8",  # coral
    "#E5E0F6",  # lavender
    "#D9E8D2",  # olive-green light
    "#F3DFB5",  # sand
    "#D6E8F4",  # sky
    "#F0D8E8",  # rose
    "#DDE9C8",  # lime light
)


def model_group_color(model_index):
    """Return the stable color assigned to a model-group index."""
    return MODEL_GROUP_COLORS[model_index % len(MODEL_GROUP_COLORS)]
