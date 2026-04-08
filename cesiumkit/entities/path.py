"""Path graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class PathGraphics(EntityGraphics):
    """A path showing an entity's trail over time."""

    lead_time: float | None = None
    trail_time: float | None = None
    width: float | None = None
    resolution: float | None = None
    material: Any = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "path"
