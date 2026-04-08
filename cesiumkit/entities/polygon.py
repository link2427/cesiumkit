"""Polygon graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.entities._base import EntityGraphics


class PolygonHierarchy(CesiumBase):
    """A polygon defined by an outer boundary and optional holes."""

    positions: list[Any]
    holes: list[PolygonHierarchy] | None = None

    def _js_class_name(self) -> str:
        return "Cesium.PolygonHierarchy"

    def to_js(self) -> str:
        pos_js = ", ".join(to_js_value(p) for p in self.positions)
        if self.holes:
            holes_js = ", ".join(h.to_js() for h in self.holes)
            return f"new Cesium.PolygonHierarchy([{pos_js}], [{holes_js}])"
        return f"new Cesium.PolygonHierarchy([{pos_js}])"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        positions_czml: list[Any] = []
        for p in self.positions:
            if hasattr(p, "to_czml"):
                czml = p.to_czml()
                # Flatten cartographicDegrees or cartesian values
                for key in ("cartographicDegrees", "cartesian"):
                    if key in czml:
                        positions_czml.extend(czml[key])
                        break
            else:
                positions_czml.append(p)
        result["cartographicDegrees"] = positions_czml
        return result


class PolygonGraphics(EntityGraphics):
    """A polygon shape on or above the surface."""

    hierarchy: Any = None
    height: float | None = None
    height_reference: Any = None
    extruded_height: float | None = None
    extruded_height_reference: Any = None
    st_rotation: float | None = None
    granularity: float | None = None
    fill: bool | None = None
    material: Any = None
    outline: bool | None = None
    outline_color: Any = None
    outline_width: float | None = None
    per_position_height: bool | None = None
    close_top: bool | None = None
    close_bottom: bool | None = None
    arc_type: Any = None
    shadows: Any = None
    classification_type: Any = None

    def _graphics_key(self) -> str:
        return "polygon"

    def to_js(self) -> str:
        """Serialize with special handling for list-based hierarchy."""
        from cesiumkit._js_serializer import camelize
        from cesiumkit.utils import JsCode

        fields = self._js_fields()

        # Convert list hierarchy to PolygonHierarchy JS expression
        if "hierarchy" in fields and isinstance(fields["hierarchy"], list):
            pos_js = ", ".join(to_js_value(p) for p in fields["hierarchy"])
            fields["hierarchy"] = JsCode(f"new Cesium.PolygonHierarchy([{pos_js}])")

        parts: list[str] = []
        for key, value in fields.items():
            js_key = camelize(key)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")
        if not parts:
            return "{}"
        return "{\n        " + ",\n        ".join(parts) + "\n    }"
