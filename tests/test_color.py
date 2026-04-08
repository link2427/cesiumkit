"""Tests for cesiumkit.color module."""

import cesiumkit
from cesiumkit.color import BLUE, RED, TRANSPARENT, WHITE, Color


class TestColor:
    def test_named_color_to_js(self):
        assert RED.to_js() == "Cesium.Color.RED"
        assert BLUE.to_js() == "Cesium.Color.BLUE"
        assert WHITE.to_js() == "Cesium.Color.WHITE"

    def test_custom_color_to_js(self):
        c = Color(red=0.5, green=0.3, blue=0.1, alpha=0.8)
        assert c.to_js() == "new Cesium.Color(0.5, 0.3, 0.1, 0.8)"

    def test_with_alpha(self):
        c = RED.with_alpha(0.5)
        assert c.to_js() == "Cesium.Color.RED.withAlpha(0.5)"

    def test_transparent(self):
        assert TRANSPARENT.to_js() == "Cesium.Color.TRANSPARENT"

    def test_from_bytes(self):
        c = Color.from_bytes(255, 0, 0)
        assert c.red == 1.0
        assert c.green == 0.0
        assert c.blue == 0.0
        assert c.alpha == 1.0

    def test_from_css_hex(self):
        c = Color.from_css("#FF0000")
        assert c.red == 1.0
        assert c.green == 0.0
        assert c.blue == 0.0

    def test_from_css_hex_with_alpha(self):
        c = Color.from_css("#FF000080")
        assert c.red == 1.0
        assert abs(c.alpha - 128 / 255) < 0.01

    def test_to_czml(self):
        czml = RED.to_czml()
        assert czml == {"rgba": [255, 0, 0, 255]}

    def test_class_level_constants(self):
        assert cesiumkit.Color.RED.to_js() == "Cesium.Color.RED"
        assert cesiumkit.Color.BLUE.to_js() == "Cesium.Color.BLUE"

    def test_from_random(self):
        c = Color.from_random(red=0.5)
        assert c.red == 0.5
        assert 0.0 <= c.green <= 1.0
        assert 0.0 <= c.blue <= 1.0
