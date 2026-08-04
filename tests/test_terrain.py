"""Tests for cesiumkit.terrain module."""

import pytest
from pydantic import ValidationError

from cesiumkit.terrain import (
    CesiumTerrainProvider,
    EllipsoidTerrainProvider,
    IonTerrainProvider,
    WmsTerrainProvider,
    WmtsTerrainProvider,
)


class TestEllipsoidTerrainProvider:
    def test_to_js(self):
        p = EllipsoidTerrainProvider()
        assert p.to_js() == "new Cesium.EllipsoidTerrainProvider()"


class TestCesiumTerrainProvider:
    def test_to_js(self):
        p = CesiumTerrainProvider(url="https://assets.cesium.com/1")
        js = p.to_js()
        assert "CesiumTerrainProvider.fromUrl" in js
        assert "https://assets.cesium.com/1" in js

    def test_to_js_with_options(self):
        js = CesiumTerrainProvider(
            url="https://assets.cesium.com/1",
            request_vertex_normals=True,
            request_water_mask=True,
        ).to_js()
        assert "requestVertexNormals: true" in js
        assert "requestWaterMask: true" in js


class TestIonTerrainProvider:
    def test_default(self):
        p = IonTerrainProvider()
        js = p.to_js()
        assert "createWorldTerrainAsync" in js

    def test_with_options(self):
        p = IonTerrainProvider(request_vertex_normals=True, request_water_mask=True)
        js = p.to_js()
        assert "createWorldTerrainAsync" in js
        assert "requestVertexNormals" in js
        assert "requestWaterMask" in js

    def test_custom_asset_uses_from_ion_asset_id(self):
        p = IonTerrainProvider(asset_id=75343)
        js = p.to_js()
        assert "CesiumTerrainProvider.fromIonAssetId(75343" in js
        assert "createWorldTerrainAsync" not in js


class TestWmsTerrainProvider:
    def test_uses_real_custom_heightmap_provider(self):
        provider = WmsTerrainProvider(
            url="https://terrain.example.com/wms?token=o'hare",
            layers="elevation",
        )
        js = provider.to_js()
        assert "new Cesium.CustomHeightmapTerrainProvider" in js
        assert "WebMapServiceTerrainProvider" not in js
        assert '"https://terrain.example.com/wms?token=o\'hare"' in js
        assert "tileXYToRectangle" in js
        assert "GetMap" in js
        assert "Float32Array" in js
        assert "-10000.0" in js

    def test_wms_130_uses_latitude_longitude_axis_order(self):
        js = WmsTerrainProvider(
            url="https://terrain.example.com/wms",
            layers="elevation",
            version="1.3.0",
        ).to_js()
        assert "[south, west, north, east]" in js
        assert "searchParams.set('crs', \"EPSG:4326\")" in js

    def test_validates_levels(self):
        with pytest.raises(ValidationError, match="maximum_level"):
            WmsTerrainProvider(
                url="https://terrain.example.com/wms",
                layers="elevation",
                minimum_level=5,
                maximum_level=4,
            )


class TestWmtsTerrainProvider:
    def test_builds_wmts_heightmap_callback(self):
        provider = WmtsTerrainProvider(
            url="https://terrain.example.com/wmts",
            layer="elevation",
            tile_matrix_set="WebMercatorQuad",
            encoding="terrarium",
        )
        js = provider.to_js()
        assert "new Cesium.CustomHeightmapTerrainProvider" in js
        assert "new Cesium.WebMercatorTilingScheme" in js
        assert "GetTile" in js
        assert "tilematrixset" in js
        assert "32768.0" in js
