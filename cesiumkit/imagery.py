"""Imagery provider types for CesiumJS map tile sources."""

from __future__ import annotations

from typing import Any

from cesiumkit.base import CesiumBase


class ImageryProvider(CesiumBase):
    """Base for all imagery providers."""

    def _js_class_name(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _js_class_name()"
        )


class IonImageryProvider(ImageryProvider):
    """Provides imagery from Cesium Ion assets."""

    asset_id: int
    access_token: str | None = None
    server: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.IonImageryProvider"


class BingMapsImageryProvider(ImageryProvider):
    """Provides imagery from Bing Maps."""

    url: str = "https://dev.virtualearth.net"
    key: str = ""
    map_style: str = "Aerial"

    def _js_class_name(self) -> str:
        return "Cesium.BingMapsImageryProvider"


class OpenStreetMapImageryProvider(ImageryProvider):
    """Provides imagery from OpenStreetMap tile servers."""

    url: str = "https://tile.openstreetmap.org/"
    file_extension: str = "png"
    maximum_level: int | None = None

    def _js_class_name(self) -> str:
        return "Cesium.OpenStreetMapImageryProvider"


class TileMapServiceImageryProvider(ImageryProvider):
    """Provides imagery from a TMS (Tile Map Service) server."""

    url: str
    file_extension: str = "png"
    minimum_level: int = 0
    maximum_level: int | None = None

    def _js_class_name(self) -> str:
        return "Cesium.TileMapServiceImageryProvider"


class UrlTemplateImageryProvider(ImageryProvider):
    """Provides imagery via a URL template with {x}, {y}, {z} placeholders."""

    url: str
    subdomains: list[str] | None = None
    minimum_level: int = 0
    maximum_level: int | None = None

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

    url: str
    layer: str
    style: str
    tile_matrix_set_id: str
    format: str = "image/png"

    def _js_class_name(self) -> str:
        return "Cesium.WebMapTileServiceImageryProvider"


class SingleTileImageryProvider(ImageryProvider):
    """Provides imagery from a single image file."""

    url: str
    rectangle: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.SingleTileImageryProvider"
