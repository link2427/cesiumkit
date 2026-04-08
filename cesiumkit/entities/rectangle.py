"""Rectangle graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class RectangleGraphics(EntityGraphics):
    """A rectangle (lat/lon extent) shape on or above the surface."""

    coordinates: Any = None
    height: float | None = None
    height_reference: Any = None
    extruded_height: float | None = None
    extruded_height_reference: Any = None
    rotation: float | None = None
    st_rotation: float | None = None
    granularity: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None
    classification_type: Any = None

    def _graphics_key(self) -> str:
        return "rectangle"
