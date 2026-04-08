"""Tests for cesiumkit.datasources module."""

from cesiumkit.color import RED
from cesiumkit.datasources import (
    CustomDataSource,
    CzmlDataSource,
    GeoJsonDataSource,
    KmlDataSource,
)


class TestCzmlDataSource:
    def test_from_url(self):
        ds = CzmlDataSource(url="https://example.com/data.czml")
        js = ds.to_js()
        assert "CzmlDataSource.load" in js
        assert "example.com/data.czml" in js

    def test_from_data(self):
        data = [{"id": "document", "version": "1.0"}]
        ds = CzmlDataSource(data=data)
        js = ds.to_js()
        assert "CzmlDataSource.load" in js
        assert "document" in js


class TestGeoJsonDataSource:
    def test_from_url(self):
        ds = GeoJsonDataSource(url="https://example.com/data.geojson")
        js = ds.to_js()
        assert "GeoJsonDataSource.load" in js
        assert "example.com/data.geojson" in js

    def test_with_options(self):
        ds = GeoJsonDataSource(
            url="https://example.com/data.geojson",
            clamp_to_ground=True,
            stroke=RED,
            stroke_width=3,
        )
        js = ds.to_js()
        assert "clampToGround: true" in js
        assert "strokeWidth: 3" in js


class TestKmlDataSource:
    def test_from_url(self):
        ds = KmlDataSource(url="https://example.com/data.kml")
        js = ds.to_js()
        assert "KmlDataSource.load" in js
        assert "example.com/data.kml" in js


class TestCustomDataSource:
    def test_with_name(self):
        ds = CustomDataSource(name="MyData")
        js = ds.to_js()
        assert "CustomDataSource" in js
        assert "MyData" in js

    def test_without_name(self):
        ds = CustomDataSource()
        js = ds.to_js()
        assert "CustomDataSource()" in js
