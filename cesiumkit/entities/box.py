"""Box graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class BoxGraphics(EntityGraphics):
    """A box (rectangular cuboid) shape."""

    dimensions: Any = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    height_reference: Any = None
    shadows: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "box"
