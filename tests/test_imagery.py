"""Tests for cesiumkit.imagery module."""

from cesiumkit.imagery import (
    BingMapsImageryProvider,
    IonImageryProvider,
    OpenStreetMapImageryProvider,
    SingleTileImageryProvider,
    UrlTemplateImageryProvider,
    WebMapServiceImageryProvider,
)


class TestIonImageryProvider:
    def test_to_js(self):
        p = IonImageryProvider(asset_id=3954)
        js = p.to_js()
        assert "IonImageryProvider" in js
        assert "3954" in js


class TestBingMapsImageryProvider:
    def test_to_js(self):
        p = BingMapsImageryProvider(key="my_key", map_style="Road")
        js = p.to_js()
        assert "BingMapsImageryProvider" in js
        assert "my_key" in js


class TestOpenStreetMapImageryProvider:
    def test_to_js(self):
        p = OpenStreetMapImageryProvider()
        js = p.to_js()
        assert "OpenStreetMapImageryProvider" in js


class TestUrlTemplateImageryProvider:
    def test_to_js(self):
        p = UrlTemplateImageryProvider(url="https://tiles.example.com/{z}/{x}/{y}.png")
        js = p.to_js()
        assert "UrlTemplateImageryProvider" in js


class TestWebMapServiceImageryProvider:
    def test_to_js(self):
        p = WebMapServiceImageryProvider(url="https://wms.example.com", layers="layer1")
        js = p.to_js()
        assert "WebMapServiceImageryProvider" in js
        assert "layer1" in js


class TestSingleTileImageryProvider:
    def test_to_js(self):
        p = SingleTileImageryProvider(url="https://example.com/tile.png")
        js = p.to_js()
        assert "SingleTileImageryProvider" in js
