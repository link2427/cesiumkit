"""Tests for cesiumkit.imagery module."""

import pytest
from pydantic import ValidationError

from cesiumkit.imagery import (
    BingMapsImageryProvider,
    IonImageryProvider,
    SingleTileImageryProvider,
    TileMapServiceImageryProvider,
    UrlTemplateImageryProvider,
    WebMapServiceImageryProvider,
    WebMapTileServiceImageryProvider,
)

_PNG_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class TestIonImageryProvider:
    def test_to_js(self):
        p = IonImageryProvider(asset_id=3954)
        js = p.to_js()
        assert js == "Cesium.IonImageryProvider.fromAssetId(3954)"
        assert p.requires_await is True

    def test_options(self):
        js = IonImageryProvider(asset_id=3954, access_token="secret", server="https://ion.example").to_js()
        assert 'accessToken: "secret"' in js
        assert 'server: "https://ion.example"' in js

    def test_asset_id_must_be_positive_plain_int(self):
        for value in (0, -1, True):
            with pytest.raises(ValidationError):
                IonImageryProvider(asset_id=value)


class TestBingMapsImageryProvider:
    def test_to_js(self):
        p = BingMapsImageryProvider(key="my_key", map_style="Road")
        js = p.to_js()
        assert js.startswith('Cesium.BingMapsImageryProvider.fromUrl("https://dev.virtualearth.net", {')
        assert 'key: "my_key"' in js
        assert 'mapStyle: "Road"' in js

    def test_key_required(self):
        with pytest.raises(ValidationError):
            BingMapsImageryProvider()


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


class TestWebMapTileServiceImageryProvider:
    def test_tile_matrix_set_uses_cesium_acronym(self):
        provider = WebMapTileServiceImageryProvider(
            url="https://example.com/wmts",
            layer="imagery",
            style="default",
            tile_matrix_set_id="WebMercatorQuad",
        )
        js = provider.to_js()
        assert 'tileMatrixSetID: "WebMercatorQuad"' in js
        assert "tileMatrixSetId" not in js


class TestSingleTileImageryProvider:
    def test_to_js(self):
        p = SingleTileImageryProvider(url="https://example.com/tile.png")
        js = p.to_js()
        assert js == 'Cesium.SingleTileImageryProvider.fromUrl("https://example.com/tile.png")'
        assert p.requires_await is True

    def test_async_base_provider_is_inserted_as_an_imagery_layer(self, playwright_browser):
        import cesiumkit
        from cesiumkit import _vendor

        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        from cesiumkit.testing import serve

        viewer = cesiumkit.Viewer(imagery_provider=SingleTileImageryProvider(url=_PNG_DATA_URI))
        with serve(viewer) as url:
            page = playwright_browser.new_page()
            try:
                page.goto(url, wait_until="load")
                page.wait_for_function(
                    """() => {
                        const layer = window.viewer?.imageryLayers.get(0);
                        return layer instanceof Cesium.ImageryLayer
                            && layer.imageryProvider instanceof Cesium.SingleTileImageryProvider
                            && layer.imageryProvider.ready !== false;
                    }""",
                    timeout=10_000,
                )
            finally:
                page.close()


class TestTileMapServiceImageryProvider:
    def test_to_js_uses_async_factory(self):
        provider = TileMapServiceImageryProvider(
            url="https://example.com/tms",
            file_extension="jpg",
            minimum_level=1,
            maximum_level=8,
        )
        js = provider.to_js()
        assert js.startswith('Cesium.TileMapServiceImageryProvider.fromUrl("https://example.com/tms", {')
        assert 'fileExtension: "jpg"' in js
        assert "minimumLevel: 1" in js
        assert "maximumLevel: 8" in js

    def test_levels_must_be_non_negative_and_ordered(self):
        with pytest.raises(ValidationError):
            TileMapServiceImageryProvider(url="https://example.com/tms", minimum_level=-1)
        with pytest.raises(ValidationError, match="maximum_level"):
            TileMapServiceImageryProvider(url="https://example.com/tms", minimum_level=4, maximum_level=3)
