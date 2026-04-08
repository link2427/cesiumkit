"""Ellipsoid graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class EllipsoidGraphics(EntityGraphics):
    """An ellipsoid (sphere/egg) shape."""

    radii: Any = None
    inner_radii: Any = None
    minimum_clock: float | None = None
    maximum_clock: float | None = None
    minimum_cone: float | None = None
    maximum_cone: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    stack_partitions: int | None = None
    slice_partitions: int | None = None
    subdivisions: int | None = None
    shadows: Any = None
    height_reference: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "ellipsoid"
