"""Plane graphics for cesiumkit — flat surfaces in 3D space."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class PlaneGraphics(EntityGraphics):
    """A plane (flat surface) positioned in 3D space.

    Useful for flight paths, range rings, radar coverage, and
    UI panels rendered in the 3D scene.
    """

    plane: Any = None  # Cartesian4 or Plane
    dimensions: Any = None  # Cartesian2
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    shadows: Any = None

    def _graphics_key(self) -> str:
        return "plane"
