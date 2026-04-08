"""Corridor graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class CorridorGraphics(EntityGraphics):
    """A corridor (extruded polyline) shape."""

    positions: list[Any] | None = None
    width: float | None = None
    height: float | None = None
    height_reference: Any = None
    extruded_height: float | None = None
    extruded_height_reference: Any = None
    corner_type: Any = None
    granularity: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None
    classification_type: Any = None

    def _graphics_key(self) -> str:
        return "corridor"
