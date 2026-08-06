"""Imagery provider types for CesiumJS map tile sources."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, model_validator

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase


def _options_js(options: list[tuple[str, Any]]) -> str:
    return "{" + ", ".join(f"{key}: {to_js_value(value)}" for key, value in options) + "}"


class ImageryProvider(CesiumBase):
    """Base for all imagery providers."""

    requires_await: ClassVar[bool] = False

    def _js_class_name(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__} must implement _js_class_name()")


class IonImageryProvider(ImageryProvider):
    """Provides imagery from Cesium Ion assets."""

    requires_await: ClassVar[bool] = True

    asset_id: int = Field(gt=0, strict=True)
    access_token: str | None = None
    server: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.IonImageryProvider"

    def to_js(self) -> str:
        options: list[tuple[str, Any]] = []
        if self.access_token is not None:
            options.append(("accessToken", self.access_token))
        if self.server is not None:
            options.append(("server", self.server))
        suffix = f", {_options_js(options)}" if options else ""
        return f"Cesium.IonImageryProvider.fromAssetId({self.asset_id}{suffix})"


class BingMapsImageryProvider(ImageryProvider):
    """Provides imagery from Bing Maps."""

    requires_await: ClassVar[bool] = True

    url: str = Field(default="https://dev.virtualearth.net", min_length=1)
    key: str = Field(min_length=1)
    map_style: str = "Aerial"

    def _js_class_name(self) -> str:
        return "Cesium.BingMapsImageryProvider"

    def to_js(self) -> str:
        options = _options_js([("key", self.key), ("mapStyle", self.map_style)])
        return f"Cesium.BingMapsImageryProvider.fromUrl({to_js_value(self.url)}, {options})"


class TileMapServiceImageryProvider(ImageryProvider):
    """Provides imagery from a TMS (Tile Map Service) server."""

    requires_await: ClassVar[bool] = True

    url: str = Field(min_length=1)
    file_extension: str = "png"
    minimum_level: int = Field(default=0, ge=0, strict=True)
    maximum_level: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def _levels_are_ordered(self) -> TileMapServiceImageryProvider:
        if self.maximum_level is not None and self.maximum_level < self.minimum_level:
            raise ValueError("maximum_level must be greater than or equal to minimum_level")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.TileMapServiceImageryProvider"

    def to_js(self) -> str:
        options: list[tuple[str, Any]] = [
            ("fileExtension", self.file_extension),
            ("minimumLevel", self.minimum_level),
        ]
        if self.maximum_level is not None:
            options.append(("maximumLevel", self.maximum_level))
        return f"Cesium.TileMapServiceImageryProvider.fromUrl({to_js_value(self.url)}, {_options_js(options)})"


class UrlTemplateImageryProvider(ImageryProvider):
    """Provides imagery via a URL template with {x}, {y}, {z} placeholders."""

    url: str = Field(min_length=1)
    subdomains: list[str] | None = None
    minimum_level: int = Field(default=0, ge=0, strict=True)
    maximum_level: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def _levels_are_ordered(self) -> UrlTemplateImageryProvider:
        if self.maximum_level is not None and self.maximum_level < self.minimum_level:
            raise ValueError("maximum_level must be greater than or equal to minimum_level")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.UrlTemplateImageryProvider"


class WebMapServiceImageryProvider(ImageryProvider):
    """Provides imagery from a WMS (Web Map Service) server."""

    url: str
    layers: str
    parameters: dict | None = None

    def _js_class_name(self) -> str:
        return "Cesium.WebMapServiceImageryProvider"


class WebMapTileServiceImageryProvider(ImageryProvider):
    """Provides imagery from a WMTS (Web Map Tile Service) server."""

    url: str = Field(min_length=1)
    layer: str = Field(min_length=1)
    style: str
    tile_matrix_set_id: str = Field(min_length=1)
    format: str = "image/png"

    def _js_class_name(self) -> str:
        return "Cesium.WebMapTileServiceImageryProvider"

    def to_js(self) -> str:
        options = _options_js(
            [
                ("url", self.url),
                ("layer", self.layer),
                ("style", self.style),
                ("tileMatrixSetID", self.tile_matrix_set_id),
                ("format", self.format),
            ]
        )
        return f"new Cesium.WebMapTileServiceImageryProvider({options})"


class SingleTileImageryProvider(ImageryProvider):
    """Provides imagery from a single image file."""

    requires_await: ClassVar[bool] = True

    url: str = Field(min_length=1)
    rectangle: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.SingleTileImageryProvider"

    def to_js(self) -> str:
        options = [] if self.rectangle is None else [("rectangle", self.rectangle)]
        suffix = f", {_options_js(options)}" if options else ""
        return f"Cesium.SingleTileImageryProvider.fromUrl({to_js_value(self.url)}{suffix})"


__all__ = [
    "BingMapsImageryProvider",
    "ImageryProvider",
    "IonImageryProvider",
    "SingleTileImageryProvider",
    "TileMapServiceImageryProvider",
    "UrlTemplateImageryProvider",
    "WebMapServiceImageryProvider",
    "WebMapTileServiceImageryProvider",
]
