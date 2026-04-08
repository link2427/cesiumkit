"""Wall graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class WallGraphics(EntityGraphics):
    """A wall shape draped along a path."""

    positions: list[Any] | None = None
    maximum_heights: list[float] | None = None
    minimum_heights: list[float] | None = None
    granularity: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "wall"
