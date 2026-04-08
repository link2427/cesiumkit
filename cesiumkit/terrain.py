"""Terrain provider types for CesiumJS elevation data sources."""

from __future__ import annotations

from cesiumkit.base import CesiumBase


class TerrainProvider(CesiumBase):
    """Base for all terrain providers."""

    def _js_class_name(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _js_class_name()"
        )


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
            opts_str = ", ".join(
                f"{k}: {str(v).lower()}" for k, v in opts.items()
            )
            return f"Cesium.createWorldTerrainAsync({{{opts_str}}})"
        return "Cesium.createWorldTerrainAsync()"
