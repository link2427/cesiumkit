"""Cylinder graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class CylinderGraphics(EntityGraphics):
    """A cylinder or cone shape."""

    length: float | None = None
    top_radius: float | None = None
    bottom_radius: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    number_of_vertical_lines: int | None = None
    slices: int | None = None
    shadows: Any = None
    height_reference: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "cylinder"
