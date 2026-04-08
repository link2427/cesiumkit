"""Polyline graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class PolylineGraphics(EntityGraphics):
    """A polyline (line strip) shape."""

    positions: list[Any] | None = None
    width: float | None = None
    material: Any = None
    clamp_to_ground: bool | None = None
    granularity: float | None = None
    shadows: Any = None
    distance_display_condition: Any = None
    classification_type: Any = None
    arc_type: Any = None
    z_index: int | None = None

    def _graphics_key(self) -> str:
        return "polyline"
