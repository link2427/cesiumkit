"""Cesium Ion token management and asset loading."""

from __future__ import annotations

import os
from math import isfinite

from pydantic import Field, field_validator, model_validator

from cesiumkit._deprecations import warn_deprecated
from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.enums import ShadowMode
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

    asset_id: int = Field(gt=0, strict=True)
    access_token: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.IonResource"

    def to_js(self) -> str:
        if self.access_token is None:
            return f"Cesium.IonResource.fromAssetId({self.asset_id})"
        return f"Cesium.IonResource.fromAssetId({self.asset_id}, {{accessToken: {to_js_value(self.access_token)}}})"


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
    show: bool | str | None = None
    point_size: float | str | None = None

    @field_validator("point_size", mode="before")
    @classmethod
    def _validate_point_size(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, bool):
            raise ValueError("point_size must be a positive number or a style expression")
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("point_size style expression must not be empty")
            return value
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise ValueError("point_size must be a positive number or a style expression") from exc
        if not isfinite(number) or number <= 0:
            raise ValueError("point_size must be positive and finite")
        return number

    def _js_class_name(self) -> str:
        return "Cesium.Cesium3DTileStyle"

    @staticmethod
    def _conditions_js(conditions: list[tuple[str, str]]) -> str:
        pairs = ", ".join(f"[{to_js_value(expr)}, {to_js_value(value)}]" for expr, value in conditions)
        return f"{{conditions: [{pairs}]}}"

    def to_js(self) -> str:
        opts: dict[str, str] = {}
        if self.color_conditions:
            opts["color"] = self._conditions_js(self.color_conditions)
        elif self.color is not None:
            opts["color"] = to_js_value(self.color)
        if self.show_conditions:
            opts["show"] = self._conditions_js(self.show_conditions)
        elif self.show is not None:
            opts["show"] = to_js_value(self.show)
        if self.point_size is not None:
            opts["pointSize"] = to_js_value(self.point_size)
        if not opts:
            return "new Cesium.Cesium3DTileStyle()"
        inner = ", ".join(f"{k}: {v}" for k, v in opts.items())
        return f"new Cesium.Cesium3DTileStyle({{{inner}}})"


class Cesium3DTileset(CesiumBase):
    """A 3D Tiles tileset added as a scene primitive.

    Options (``show``, ``maximum_screen_space_error``, ``cache_bytes``,
    ``shadows``) are serialized only when explicitly provided; defaults stay
    implicit for compact output. The 0.x ``maximum_memory_usage`` option is a
    deprecated MiB compatibility shim that maps to ``cache_bytes``.
    """

    url: str | None = Field(default=None, min_length=1)
    ion_asset_id: int | None = Field(default=None, gt=0, strict=True)
    show: bool = True
    maximum_screen_space_error: float = Field(default=16.0, gt=0, allow_inf_nan=False)
    cache_bytes: int | None = Field(default=None, gt=0, strict=True)
    maximum_memory_usage: int | None = Field(default=None, gt=0, strict=True, exclude=True)
    shadows: ShadowMode | None = None
    style: Cesium3DTileStyle | None = None
    clipping_planes: ClippingPlaneCollection | None = None

    @field_validator("maximum_memory_usage")
    @classmethod
    def _warn_for_legacy_memory_limit(cls, value: int | None) -> int | None:
        warn_deprecated(
            "Cesium3DTileset(maximum_memory_usage=...)",
            alternative="Cesium3DTileset(cache_bytes=...)",
        )
        return value

    @model_validator(mode="after")
    def _exactly_one_source(self) -> Cesium3DTileset:
        if (self.url is None) == (self.ion_asset_id is None):
            raise ValueError("exactly one of url or ion_asset_id must be provided")
        if self.cache_bytes is not None and self.maximum_memory_usage is not None:
            raise ValueError("cache_bytes and maximum_memory_usage cannot both be set")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.Cesium3DTileset"

    def _tileset_options_js(self) -> str:
        """Serialize only options the caller explicitly set."""
        opts: list[str] = []
        if "maximum_screen_space_error" in self.model_fields_set:
            opts.append(f"maximumScreenSpaceError: {self.maximum_screen_space_error}")
        if self.maximum_memory_usage is not None:
            opts.append(f"cacheBytes: {self.maximum_memory_usage * 1024 * 1024}")
        elif "cache_bytes" in self.model_fields_set and self.cache_bytes is not None:
            opts.append(f"cacheBytes: {self.cache_bytes}")
        if "show" in self.model_fields_set:
            opts.append(f"show: {str(self.show).lower()}")
        if "shadows" in self.model_fields_set and self.shadows is not None:
            opts.append(f"shadows: {to_js_value(self.shadows)}")
        if self.clipping_planes is not None:
            opts.append(f"clippingPlanes: {self.clipping_planes.to_js()}")
        return "{" + ", ".join(opts) + "}" if opts else ""

    def to_js(self) -> str:
        if self.ion_asset_id is not None:
            create = f"Cesium.Cesium3DTileset.fromIonAssetId({self.ion_asset_id}"
        else:
            create = f"Cesium.Cesium3DTileset.fromUrl({to_js_value(self.url)}"
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
