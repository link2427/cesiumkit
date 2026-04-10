"""Polyline graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from pydantic import field_validator

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

    @field_validator("positions", mode="before")
    @classmethod
    def _coerce_shapely_positions(cls, value: Any) -> Any:
        """Auto-convert shapely LineString/LinearRing to a list of Cartesian3FromDegrees (WGS84)."""
        from cesiumkit._shapely import is_shapely_geom, shapely_line_to_positions

        if is_shapely_geom(value) and value.geom_type in ("LineString", "LinearRing"):
            return shapely_line_to_positions(value)
        return value

    def _graphics_key(self) -> str:
        return "polyline"
