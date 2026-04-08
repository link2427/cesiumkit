"""Point graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class PointGraphics(EntityGraphics):
    """A point (pixel-sized dot) attached to an entity's position."""

    pixel_size: float | None = None
    color: Any = None
    outline_color: Any = None
    outline_width: float | None = None
    height_reference: Any = None
    scale_by_distance: Any = None
    translucency_by_distance: Any = None
    distance_display_condition: Any = None
    disable_depth_test_distance: float | None = None

    def _graphics_key(self) -> str:
        return "point"
