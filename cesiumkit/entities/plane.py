"""Plane graphics for cesiumkit — flat surfaces in 3D space."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.entities._base import EntityGraphics


class Plane(CesiumBase):
    """A plane represented by a normal vector and signed distance."""

    normal: Any
    distance: float = Field(allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "Cesium.Plane"

    def to_js(self) -> str:
        return f"new Cesium.Plane({to_js_value(self.normal)}, {self.distance})"


class PlaneGraphics(EntityGraphics):
    """A plane (flat surface) positioned in 3D space.

    Useful for flight paths, range rings, radar coverage, and
    UI panels rendered in the 3D scene.
    """

    plane: Any = None
    dimensions: Any = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None

    def _graphics_key(self) -> str:
        return "plane"
