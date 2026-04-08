"""Tests for cesiumkit.terrain module."""

from cesiumkit.terrain import (
    CesiumTerrainProvider,
    EllipsoidTerrainProvider,
    IonTerrainProvider,
)


class TestEllipsoidTerrainProvider:
    def test_to_js(self):
        p = EllipsoidTerrainProvider()
        assert p.to_js() == "new Cesium.EllipsoidTerrainProvider()"


class TestCesiumTerrainProvider:
    def test_to_js(self):
        p = CesiumTerrainProvider(url="https://assets.cesium.com/1")
        js = p.to_js()
        assert "CesiumTerrainProvider" in js


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
