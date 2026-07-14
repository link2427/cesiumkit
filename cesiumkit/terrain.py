"""Terrain provider types for CesiumJS elevation data sources."""

from __future__ import annotations

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

    url: str
    request_water_mask: bool = False
    request_vertex_normals: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.CesiumTerrainProvider"


class IonTerrainProvider(TerrainProvider):
    """Provides terrain from Cesium Ion (default: Cesium World Terrain)."""

    asset_id: int = 1
    request_water_mask: bool = False
    request_vertex_normals: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.CesiumTerrainProvider"

    def to_js(self) -> str:
        opts: dict[str, bool] = {}
        if self.request_water_mask:
            opts["requestWaterMask"] = True
        if self.request_vertex_normals:
            opts["requestVertexNormals"] = True
        if opts:
            opts_str = ", ".join(f"{k}: {str(v).lower()}" for k, v in opts.items())
            return f"Cesium.createWorldTerrainAsync({{{opts_str}}})"
        return "Cesium.createWorldTerrainAsync()"


class WmsTerrainProvider(TerrainProvider):
    """Provides terrain data from a WMS (Web Map Service) elevation endpoint.

    Useful for organizations serving terrain via WMS rather than
    Cesium's quantized-mesh format.
    """

    url: str
    layers: str = ""
    format: str = "image/png"
    minimum_level: int = 0
    maximum_level: int = 15

    def _js_class_name(self) -> str:
        return "Cesium.WebMapServiceTerrainProvider"

    def to_js(self) -> str:
        opts = []
        opts.append(f"url: '{self.url}'")
        if self.layers:
            opts.append(f"layers: '{self.layers}'")
        opts.append(f"format: '{self.format}'")
        opts.append(f"minimumLevel: {self.minimum_level}")
        opts.append(f"maximumLevel: {self.maximum_level}")
        return f"new Cesium.WebMapServiceTerrainProvider({{{', '.join(opts)}}})"
