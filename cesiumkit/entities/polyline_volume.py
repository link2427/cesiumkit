"""Polyline volume graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class PolylineVolumeGraphics(EntityGraphics):
    """A polyline with a 2D cross-section shape extruded along it."""

    positions: list[Any] | None = None
    shape: list[Any] | None = None
    corner_type: Any = None
    granularity: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "polylineVolume"
