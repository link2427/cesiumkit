"""Terrain provider types for CesiumJS elevation data sources."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase


class TerrainProvider(CesiumBase):
    """Base for all terrain providers."""

    def _js_class_name(self) -> str:
        raise NotImplementedError(f"{self.__class__.__name__} must implement _js_class_name()")


class EllipsoidTerrainProvider(TerrainProvider):
    """A terrain provider that provides no elevation (smooth ellipsoid)."""

    def _js_class_name(self) -> str:
        return "Cesium.EllipsoidTerrainProvider"

    def to_js(self) -> str:
        return "new Cesium.EllipsoidTerrainProvider()"


class CesiumTerrainProvider(TerrainProvider):
    """Provides terrain data from a Cesium terrain server."""

    url: str = Field(min_length=1)
    request_water_mask: bool = False
    request_vertex_normals: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.CesiumTerrainProvider"

    def to_js(self) -> str:
        """Serialize to an async CesiumTerrainProvider.fromUrl(...) call."""
        opts: list[str] = []
        if self.request_water_mask:
            opts.append("requestWaterMask: true")
        if self.request_vertex_normals:
            opts.append("requestVertexNormals: true")
        options = f", {{{', '.join(opts)}}}" if opts else ""
        return f"Cesium.CesiumTerrainProvider.fromUrl({to_js_value(self.url)}{options})"


class IonTerrainProvider(TerrainProvider):
    """Provides terrain from Cesium Ion (default: Cesium World Terrain)."""

    asset_id: int = Field(default=1, gt=0, strict=True)
    request_water_mask: bool = False
    request_vertex_normals: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.CesiumTerrainProvider"

    def to_js(self) -> str:
        opts: dict[str, str] = {}
        if self.request_water_mask:
            opts["requestWaterMask"] = "true"
        if self.request_vertex_normals:
            opts["requestVertexNormals"] = "true"
        opts_js = "{" + ", ".join(f"{k}: {v}" for k, v in opts.items()) + "}" if opts else "{}"
        if self.asset_id == 1:
            # createWorldTerrainAsync is the async equivalent of the world
            # terrain asset (asset id 1).
            return f"Cesium.createWorldTerrainAsync({opts_js})"
        return f"Cesium.CesiumTerrainProvider.fromIonAssetId({self.asset_id}, {opts_js})"


class _ImageHeightmapTerrainProvider(TerrainProvider):
    """Shared adapter from encoded elevation images to Cesium height arrays."""

    tile_width: int = Field(default=65, ge=2, le=2048)
    tile_height: int = Field(default=65, ge=2, le=2048)
    minimum_level: int = Field(default=0, ge=0)
    maximum_level: int = Field(default=15, ge=0)
    encoding: Literal["terrain-rgb", "terrarium", "grayscale"] = "terrain-rgb"
    height_scale: float = Field(default=1.0, allow_inf_nan=False)
    height_offset: float = Field(default=0.0, allow_inf_nan=False)
    credit: str | None = None

    @model_validator(mode="after")
    def _validate_levels(self) -> _ImageHeightmapTerrainProvider:
        if self.maximum_level < self.minimum_level:
            raise ValueError("maximum_level must be greater than or equal to minimum_level")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.CustomHeightmapTerrainProvider"

    def _height_expression(self) -> str:
        if self.encoding == "terrain-rgb":
            raw = "-10000.0 + (red * 65536.0 + green * 256.0 + blue) * 0.1"
        elif self.encoding == "terrarium":
            raw = "red * 256.0 + green + blue / 256.0 - 32768.0"
        else:
            raw = "red"
        return f"({raw}) * {self.height_scale} + {self.height_offset}"

    def _custom_provider_js(self, request_url_js: str, *, tiling_scheme: str) -> str:
        credit = f", credit: {to_js_value(self.credit)}" if self.credit is not None else ""
        transparent_height = self.height_offset
        return (
            "(() => {"
            f"const tilingScheme = new Cesium.{tiling_scheme}();"
            "return new Cesium.CustomHeightmapTerrainProvider({"
            f"width: {self.tile_width}, height: {self.tile_height}, tilingScheme{credit},"
            "callback: async (x, y, level) => {"
            f"if (level < {self.minimum_level} || level > {self.maximum_level}) return undefined;"
            f"{request_url_js}"
            "const response = await fetch(requestUrl, {mode: 'cors'});"
            "if (!response.ok) throw new Error(`Terrain request failed: ${response.status}`);"
            "const bitmap = await createImageBitmap(await response.blob());"
            "const canvas = document.createElement('canvas');"
            f"canvas.width = {self.tile_width}; canvas.height = {self.tile_height};"
            "const context = canvas.getContext('2d', {willReadFrequently: true});"
            "context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);"
            "if (bitmap.close) bitmap.close();"
            "const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;"
            f"const heights = new Float32Array({self.tile_width * self.tile_height});"
            "for (let index = 0; index < heights.length; index += 1) {"
            "const offset = index * 4;"
            "const red = pixels[offset]; const green = pixels[offset + 1]; const blue = pixels[offset + 2];"
            f"heights[index] = pixels[offset + 3] === 0 ? {transparent_height} : {self._height_expression()};"
            "}"
            "return heights;"
            "}"
            "});"
            "})()"
        )


class WmsTerrainProvider(_ImageHeightmapTerrainProvider):
    """Adapt encoded WMS elevation images into Cesium heightmap terrain.

    The WMS layer must render elevations as Terrain-RGB, Terrarium, or
    grayscale pixels and permit browser CORS requests.
    """

    url: str = Field(min_length=1)
    layers: str = Field(min_length=1)
    format: str = "image/png"
    styles: str = ""
    version: Literal["1.1.1", "1.3.0"] = "1.1.1"
    crs: str = "EPSG:4326"

    def to_js(self) -> str:
        if self.version == "1.3.0" and self.crs.upper() == "EPSG:4326":
            bbox = "[south, west, north, east]"
            reference_parameter = "crs"
        else:
            bbox = "[west, south, east, north]"
            reference_parameter = "crs" if self.version == "1.3.0" else "srs"

        request_url_js = (
            "const rectangle = tilingScheme.tileXYToRectangle(x, y, level);"
            "const west = Cesium.Math.toDegrees(rectangle.west);"
            "const south = Cesium.Math.toDegrees(rectangle.south);"
            "const east = Cesium.Math.toDegrees(rectangle.east);"
            "const north = Cesium.Math.toDegrees(rectangle.north);"
            f"const requestUrl = new URL({to_js_value(self.url)}, window.location.href);"
            "requestUrl.searchParams.set('service', 'WMS');"
            "requestUrl.searchParams.set('request', 'GetMap');"
            f"requestUrl.searchParams.set('version', {to_js_value(self.version)});"
            f"requestUrl.searchParams.set('layers', {to_js_value(self.layers)});"
            f"requestUrl.searchParams.set('styles', {to_js_value(self.styles)});"
            f"requestUrl.searchParams.set('format', {to_js_value(self.format)});"
            f"requestUrl.searchParams.set('{reference_parameter}', {to_js_value(self.crs)});"
            f"requestUrl.searchParams.set('width', '{self.tile_width}');"
            f"requestUrl.searchParams.set('height', '{self.tile_height}');"
            f"requestUrl.searchParams.set('bbox', {bbox}.join(','));"
        )
        return self._custom_provider_js(request_url_js, tiling_scheme="GeographicTilingScheme")


class WmtsTerrainProvider(_ImageHeightmapTerrainProvider):
    """Adapt encoded WMTS elevation tiles into Cesium heightmap terrain."""

    url: str = Field(min_length=1)
    layer: str = Field(min_length=1)
    tile_matrix_set: str = Field(min_length=1)
    format: str = "image/png"
    style: str = ""
    tiling_scheme: Literal["geographic", "web_mercator"] = "web_mercator"

    def to_js(self) -> str:
        request_url_js = (
            f"const requestUrl = new URL({to_js_value(self.url)}, window.location.href);"
            "requestUrl.searchParams.set('service', 'WMTS');"
            "requestUrl.searchParams.set('request', 'GetTile');"
            "requestUrl.searchParams.set('version', '1.0.0');"
            f"requestUrl.searchParams.set('layer', {to_js_value(self.layer)});"
            f"requestUrl.searchParams.set('style', {to_js_value(self.style)});"
            f"requestUrl.searchParams.set('format', {to_js_value(self.format)});"
            f"requestUrl.searchParams.set('tilematrixset', {to_js_value(self.tile_matrix_set)});"
            "requestUrl.searchParams.set('tilematrix', String(level));"
            "requestUrl.searchParams.set('tilerow', String(y));"
            "requestUrl.searchParams.set('tilecol', String(x));"
        )
        scheme = "GeographicTilingScheme" if self.tiling_scheme == "geographic" else "WebMercatorTilingScheme"
        return self._custom_provider_js(request_url_js, tiling_scheme=scheme)


__all__ = [
    "CesiumTerrainProvider",
    "EllipsoidTerrainProvider",
    "IonTerrainProvider",
    "TerrainProvider",
    "WmsTerrainProvider",
    "WmtsTerrainProvider",
]
