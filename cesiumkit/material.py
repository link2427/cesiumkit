"""Material types for cesiumkit, matching CesiumJS material property classes."""

from __future__ import annotations

from typing import Any

from cesiumkit._js_serializer import camelize, to_js_value
from cesiumkit.base import CesiumBase


class MaterialBase(CesiumBase):
    """Abstract base for all materials."""

    def _js_class_name(self) -> str:
        raise NotImplementedError


class SolidColorMaterial(MaterialBase):
    """A material that fills the surface with a solid color."""

    color: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.ColorMaterialProperty"

    def to_js(self) -> str:
        # Cesium shorthand: material can be just a color expression
        if self.color is not None and hasattr(self.color, "to_js"):
            return self.color.to_js()
        if self.color is not None:
            return to_js_value(self.color)
        return "undefined"

    def to_czml(self) -> dict:
        if self.color is not None and hasattr(self.color, "to_czml"):
            return {"solidColor": {"color": self.color.to_czml()}}
        return {}


class ImageMaterial(MaterialBase):
    """A material that fills the surface with an image."""

    image: str | None = None
    repeat: Any = None  # Cartesian2
    color: Any = None
    transparent: bool | None = None

    def _js_class_name(self) -> str:
        return "Cesium.ImageMaterialProperty"

    def to_js(self) -> str:
        fields = self._js_fields()
        parts: list[str] = []
        for key, value in fields.items():
            js_key = camelize(key)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")
        if not parts:
            return f"new {self._js_class_name()}()"
        opts = "{\n    " + ",\n    ".join(parts) + "\n}"
        return f"new {self._js_class_name()}({opts})"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.image is not None:
            result["image"] = self.image
        if self.repeat is not None and hasattr(self.repeat, "to_czml"):
            result["repeat"] = self.repeat.to_czml()
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        if self.transparent is not None:
            result["transparent"] = self.transparent
        return {"image": result} if result else {}


class GridMaterial(MaterialBase):
    """A material that fills the surface with a grid pattern."""

    color: Any = None
    cell_alpha: float | None = None
    line_count: Any = None  # Cartesian2
    line_thickness: Any = None  # Cartesian2
    line_offset: Any = None  # Cartesian2

    def _js_class_name(self) -> str:
        return "Cesium.GridMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        if self.cell_alpha is not None:
            result["cellAlpha"] = self.cell_alpha
        if self.line_count is not None and hasattr(self.line_count, "to_czml"):
            result["lineCount"] = self.line_count.to_czml()
        if self.line_thickness is not None and hasattr(self.line_thickness, "to_czml"):
            result["lineThickness"] = self.line_thickness.to_czml()
        if self.line_offset is not None and hasattr(self.line_offset, "to_czml"):
            result["lineOffset"] = self.line_offset.to_czml()
        return {"grid": result} if result else {}


class StripeMaterial(MaterialBase):
    """A material that fills the surface with alternating stripes."""

    orientation: Any = None  # StripeOrientation enum
    even_color: Any = None
    odd_color: Any = None
    offset: float | None = None
    repeat: float | None = None

    def _js_class_name(self) -> str:
        return "Cesium.StripeMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.orientation is not None:
            result["orientation"] = str(self.orientation)
        if self.even_color is not None and hasattr(self.even_color, "to_czml"):
            result["evenColor"] = self.even_color.to_czml()
        if self.odd_color is not None and hasattr(self.odd_color, "to_czml"):
            result["oddColor"] = self.odd_color.to_czml()
        if self.offset is not None:
            result["offset"] = self.offset
        if self.repeat is not None:
            result["repeat"] = self.repeat
        return {"stripe": result} if result else {}


class CheckerboardMaterial(MaterialBase):
    """A material that fills the surface with a checkerboard pattern."""

    even_color: Any = None
    odd_color: Any = None
    repeat: Any = None  # Cartesian2

    def _js_class_name(self) -> str:
        return "Cesium.CheckerboardMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.even_color is not None and hasattr(self.even_color, "to_czml"):
            result["evenColor"] = self.even_color.to_czml()
        if self.odd_color is not None and hasattr(self.odd_color, "to_czml"):
            result["oddColor"] = self.odd_color.to_czml()
        if self.repeat is not None and hasattr(self.repeat, "to_czml"):
            result["repeat"] = self.repeat.to_czml()
        return {"checkerboard": result} if result else {}


class PolylineGlowMaterial(MaterialBase):
    """A material that makes a polyline glow."""

    color: Any = None
    glow_power: float | None = None
    taper_power: float | None = None

    def _js_class_name(self) -> str:
        return "Cesium.PolylineGlowMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        if self.glow_power is not None:
            result["glowPower"] = self.glow_power
        if self.taper_power is not None:
            result["taperPower"] = self.taper_power
        return {"polylineGlow": result} if result else {}


class PolylineArrowMaterial(MaterialBase):
    """A material that renders a polyline as an arrow."""

    color: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.PolylineArrowMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        return {"polylineArrow": result} if result else {}


class PolylineDashMaterial(MaterialBase):
    """A material that renders a polyline with dashes."""

    color: Any = None
    gap_color: Any = None
    dash_length: float | None = None
    dash_pattern: int | None = None

    def _js_class_name(self) -> str:
        return "Cesium.PolylineDashMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        if self.gap_color is not None and hasattr(self.gap_color, "to_czml"):
            result["gapColor"] = self.gap_color.to_czml()
        if self.dash_length is not None:
            result["dashLength"] = self.dash_length
        if self.dash_pattern is not None:
            result["dashPattern"] = self.dash_pattern
        return {"polylineDash": result} if result else {}


class PolylineOutlineMaterial(MaterialBase):
    """A material that renders a polyline with an outline."""

    color: Any = None
    outline_color: Any = None
    outline_width: float | None = None

    def _js_class_name(self) -> str:
        return "Cesium.PolylineOutlineMaterialProperty"

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.color is not None and hasattr(self.color, "to_czml"):
            result["color"] = self.color.to_czml()
        if self.outline_color is not None and hasattr(self.outline_color, "to_czml"):
            result["outlineColor"] = self.outline_color.to_czml()
        if self.outline_width is not None:
            result["outlineWidth"] = self.outline_width
        return {"polylineOutline": result} if result else {}
