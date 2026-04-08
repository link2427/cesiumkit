"""Billboard graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class BillboardGraphics(EntityGraphics):
    """A billboard (2D image) attached to an entity's position."""

    image: str | None = None
    scale: float | None = None
    pixel_offset: Any = None
    eye_offset: Any = None
    horizontal_origin: Any = None
    vertical_origin: Any = None
    height_reference: Any = None
    color: Any = None
    rotation: float | None = None
    aligned_axis: Any = None
    size_in_meters: bool | None = None
    width: float | None = None
    height: float | None = None
    scale_by_distance: Any = None
    translucency_by_distance: Any = None
    distance_display_condition: Any = None
    disable_depth_test_distance: float | None = None

    def _graphics_key(self) -> str:
        return "billboard"
