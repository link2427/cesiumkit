"""Cesium Ion token management and asset loading."""

from __future__ import annotations

import json
import os
from typing import Any

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.scene import ClippingPlaneCollection


class Ion:
    """Manages Cesium Ion token and asset loading."""

    _default_token: str | None = None

    @classmethod
    def set_default_token(cls, token: str) -> None:
        """Set the default Ion access token."""
        cls._default_token = token

    @classmethod
    def get_default_token(cls) -> str | None:
        """Get the default Ion token, falling back to CESIUM_ION_TOKEN env var."""
        return cls._default_token or os.environ.get("CESIUM_ION_TOKEN")


class IonResource(CesiumBase):
    """Reference to a Cesium Ion asset resource."""

    asset_id: int
    access_token: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.IonResource"

    def to_js(self) -> str:
        return f"Cesium.IonResource.fromAssetId({self.asset_id})"


class Cesium3DTileStyle(CesiumBase):
    """Style a 3D Tiles tileset with per-feature conditions.

    Emits ``new Cesium.Cesium3DTileStyle({...})`` (the class was renamed from
    Cesium3DTilesetStyle in recent Cesium releases). Each condition is a
    ``(expression, value)`` pair evaluated per feature, e.g.::

        Cesium3DTileStyle(color_conditions=[
            ("${Height} < 100", "color('red')"),
            ("true", "color('blue')"),
        ])

    ``color`` / ``show`` accept either a conditions list or a static value
    string; ``point_size`` sets the point size for point features.
    """

    color_conditions: list[tuple[str, str]] | None = None
    color: str | None = None
    show_conditions: list[tuple[str, str]] | None = None
    point_size: float | None = None

    def _js_class_name(self) -> str:
        return "Cesium.Cesium3DTileStyle"

    @staticmethod
    def _conditions_js(conditions: list[tuple[str, str]]) -> str:
        pairs = ", ".join(f"[{json.dumps(expr)}, {value}]" for expr, value in conditions)
        return f"{{conditions: [{pairs}]}}"

    def to_js(self) -> str:
        opts: dict[str, str] = {}
        if self.color_conditions:
            opts["color"] = self._conditions_js(self.color_conditions)
        elif self.color is not None:
            opts["color"] = self.color
        if self.show_conditions:
            opts["show"] = self._conditions_js(self.show_conditions)
        if self.point_size is not None:
            opts["pointSize"] = repr(self.point_size)
        if not opts:
            return "new Cesium.Cesium3DTileStyle()"
        inner = ", ".join(f"{k}: {v}" for k, v in opts.items())
        return f"new Cesium.Cesium3DTileStyle({{{inner}}})"


class Cesium3DTileset(CesiumBase):
    """A 3D Tiles tileset added as a scene primitive.

    Options (``show``, ``maximum_screen_space_error``,
    ``maximum_memory_usage``, ``shadows``) are serialized only when
    explicitly provided; defaults stay implicit for compact output.
    """

    url: str | None = None
    ion_asset_id: int | None = None
    show: bool = True
    maximum_screen_space_error: float = 16.0
    maximum_memory_usage: int | None = None
    shadows: Any = None
    style: Cesium3DTileStyle | None = None
    clipping_planes: ClippingPlaneCollection | None = None

    def _js_class_name(self) -> str:
        return "Cesium.Cesium3DTileset"

    def _tileset_options_js(self) -> str:
        """Serialize only options the caller explicitly set."""
        opts: list[str] = []
        if "maximum_screen_space_error" in self.model_fields_set:
            opts.append(f"maximumScreenSpaceError: {self.maximum_screen_space_error}")
        if "maximum_memory_usage" in self.model_fields_set and self.maximum_memory_usage is not None:
            opts.append(f"maximumMemoryUsage: {self.maximum_memory_usage}")
        if "show" in self.model_fields_set:
            opts.append(f"show: {str(self.show).lower()}")
        if "shadows" in self.model_fields_set and self.shadows is not None:
            opts.append(f"shadows: {to_js_value(self.shadows)}")
        if self.clipping_planes is not None:
            opts.append(f"clippingPlanes: {self.clipping_planes.to_js()}")
        return ", ".join(opts)

    def to_js(self) -> str:
        if self.ion_asset_id:
            create = f"Cesium.Cesium3DTileset.fromIonAssetId({self.ion_asset_id}"
        elif self.url:
            create = f"Cesium.Cesium3DTileset.fromUrl({json.dumps(self.url)}"
        else:
            raise ValueError("Either url or ion_asset_id must be provided")
        opts = self._tileset_options_js()
        create = f"{create}, {opts})" if opts else f"{create})"
        if self.style is None:
            return create
        return (
            "(async () => {\n"
            f"    const tileset = await {create};\n"
            f"    tileset.style = {self.style.to_js()};\n"
            "    return tileset;\n"
            "})()"
        )


__all__ = [
    "Cesium3DTileStyle",
    "Cesium3DTileset",
    "Ion",
    "IonResource",
]
