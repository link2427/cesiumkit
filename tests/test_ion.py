"""Tests for Cesium ion resources, 3D Tiles styles, and tilesets."""

import pytest
from pydantic import ValidationError

import cesiumkit
from cesiumkit._deprecations import CesiumkitDeprecationWarning


class TestIonResource:
    def test_access_token_is_forwarded_safely(self):
        js = cesiumkit.IonResource(asset_id=42, access_token='token"</script>').to_js()
        assert js == 'Cesium.IonResource.fromAssetId(42, {accessToken: "token\\"\\u003c/script\\u003e"})'

    @pytest.mark.parametrize("asset_id", [0, -1, True])
    def test_asset_id_must_be_positive_plain_int(self, asset_id):
        with pytest.raises(ValidationError):
            cesiumkit.IonResource(asset_id=asset_id)


class TestCesium3DTileStyle:
    def test_expressions_are_style_strings(self):
        style = cesiumkit.Cesium3DTileStyle(
            color_conditions=[("${Height} < 100", "color('red')"), ("true", "color('blue')")],
            show_conditions=[("${visible} === true", "true"), ("true", "false")],
            point_size=4,
        )
        js = style.to_js()
        assert '["${Height} \\u003c 100", "color(\'red\')"]' in js
        assert '["${visible} === true", "true"]' in js
        assert "pointSize: 4.0" in js

    def test_static_color_is_a_string(self):
        assert cesiumkit.Cesium3DTileStyle(color="color('red')").to_js() == (
            "new Cesium.Cesium3DTileStyle({color: \"color('red')\"})"
        )

    def test_static_show_and_point_size_expression_are_style_strings(self):
        style = cesiumkit.Cesium3DTileStyle(
            show="${Height} > 0",
            point_size="${Temperature} * 2.0",
        )
        assert style.to_js() == (
            'new Cesium.Cesium3DTileStyle({show: "${Height} \\u003e 0", pointSize: "${Temperature} * 2.0"})'
        )

    def test_static_show_accepts_a_boolean(self):
        assert cesiumkit.Cesium3DTileStyle(show=False).to_js() == ("new Cesium.Cesium3DTileStyle({show: false})")

    def test_show_conditions_take_precedence_over_static_show(self):
        style = cesiumkit.Cesium3DTileStyle(
            show="false",
            show_conditions=[("${visible}", "true")],
        )
        assert 'show: {conditions: [["${visible}", "true"]]}' in style.to_js()
        assert 'show: "false"' not in style.to_js()

    @pytest.mark.parametrize("point_size", [0, -1, float("inf"), True, ""])
    def test_point_size_must_be_positive_and_finite(self, point_size):
        with pytest.raises(ValidationError):
            cesiumkit.Cesium3DTileStyle(point_size=point_size)


class TestCesium3DTileset:
    def test_url_options_are_wrapped_in_an_object(self):
        tileset = cesiumkit.Cesium3DTileset(
            url="https://example.com/tileset.json",
            maximum_screen_space_error=4,
            cache_bytes=536_870_912,
            show=False,
            shadows=cesiumkit.ShadowMode.CAST_ONLY,
        )
        assert tileset.to_js() == (
            'Cesium.Cesium3DTileset.fromUrl("https://example.com/tileset.json", '
            "{maximumScreenSpaceError: 4.0, cacheBytes: 536870912, show: false, "
            "shadows: Cesium.ShadowMode.CAST_ONLY})"
        )

    def test_ion_options_are_wrapped_in_an_object(self):
        assert cesiumkit.Cesium3DTileset(ion_asset_id=75343, cache_bytes=1000).to_js() == (
            "Cesium.Cesium3DTileset.fromIonAssetId(75343, {cacheBytes: 1000})"
        )

    def test_legacy_memory_megabytes_map_to_cache_bytes_with_warning(self):
        with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
            tileset = cesiumkit.Cesium3DTileset(
                url="https://example.com/tileset.json",
                maximum_memory_usage=512,
            )
        assert "cacheBytes: 536870912" in tileset.to_js()

    def test_legacy_and_current_memory_options_are_mutually_exclusive(self):
        with pytest.warns(CesiumkitDeprecationWarning):
            with pytest.raises(ValidationError, match="cannot both be set"):
                cesiumkit.Cesium3DTileset(
                    url="https://example.com/tileset.json",
                    cache_bytes=1,
                    maximum_memory_usage=1,
                )

    def test_legacy_memory_assignment_warns_and_serializes(self):
        tileset = cesiumkit.Cesium3DTileset(url="https://example.com/tileset.json")
        with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
            tileset.maximum_memory_usage = 512
        assert "cacheBytes: 536870912" in tileset.to_js()

        with pytest.raises(ValidationError, match="cannot both be set"):
            tileset.cache_bytes = 1
        assert tileset.cache_bytes is None
        assert tileset.maximum_memory_usage == 512

    @pytest.mark.parametrize(
        "kwargs",
        [
            {},
            {"url": "https://example.com/tileset.json", "ion_asset_id": 1},
            {"url": ""},
            {"ion_asset_id": True},
        ],
    )
    def test_exactly_one_valid_source_is_required(self, kwargs):
        with pytest.raises(ValidationError):
            cesiumkit.Cesium3DTileset(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"maximum_screen_space_error": 0},
            {"maximum_screen_space_error": float("nan")},
            {"cache_bytes": 0},
            {"cache_bytes": True},
            {"maximum_memory_usage": 0},
            {"maximum_memory_usage": True},
        ],
    )
    def test_numeric_options_are_validated(self, kwargs):
        with pytest.raises(ValidationError):
            cesiumkit.Cesium3DTileset(url="https://example.com/tileset.json", **kwargs)
