"""Label graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class LabelGraphics(EntityGraphics):
    """A text label attached to an entity's position."""

    text: str | None = None
    font: str | None = None
    style: Any = None
    fill_color: Any = None
    outline_color: Any = None
    outline_width: float | None = None
    show_background: bool | None = None
    background_color: Any = None
    background_padding: Any = None
    scale: float | None = None
    pixel_offset: Any = None
    eye_offset: Any = None
    horizontal_origin: Any = None
    vertical_origin: Any = None
    height_reference: Any = None
    distance_display_condition: Any = None
    disable_depth_test_distance: float | None = None

    def _graphics_key(self) -> str:
        return "label"
