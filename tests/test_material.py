"""Tests for cesiumkit.material module."""

from cesiumkit.color import BLUE, RED, WHITE
from cesiumkit.material import (
    GridMaterial,
    ImageMaterial,
    PolylineArrowMaterial,
    PolylineDashMaterial,
    PolylineGlowMaterial,
    PolylineOutlineMaterial,
    SolidColorMaterial,
    StripeMaterial,
)


class TestSolidColorMaterial:
    def test_to_js(self):
        m = SolidColorMaterial(color=RED)
        js = m.to_js()
        assert "Cesium.Color.RED" in js


class TestImageMaterial:
    def test_to_js(self):
        m = ImageMaterial(image="https://example.com/texture.png")
        js = m.to_js()
        assert "ImageMaterialProperty" in js
        assert "example.com/texture.png" in js


class TestGridMaterial:
    def test_to_js(self):
        m = GridMaterial(color=WHITE)
        js = m.to_js()
        assert "GridMaterialProperty" in js


class TestStripeMaterial:
    def test_to_js(self):
        m = StripeMaterial(even_color=RED, odd_color=BLUE, repeat=5.0)
        js = m.to_js()
        assert "StripeMaterialProperty" in js
        assert "Cesium.Color.RED" in js
        assert "Cesium.Color.BLUE" in js


class TestPolylineGlowMaterial:
    def test_to_js(self):
        m = PolylineGlowMaterial(color=RED, glow_power=0.2)
        js = m.to_js()
        assert "PolylineGlowMaterialProperty" in js
        assert "0.2" in js


class TestPolylineArrowMaterial:
    def test_to_js(self):
        m = PolylineArrowMaterial(color=RED)
        js = m.to_js()
        assert "PolylineArrowMaterialProperty" in js


class TestPolylineDashMaterial:
    def test_to_js(self):
        m = PolylineDashMaterial(color=RED, dash_length=16.0)
        js = m.to_js()
        assert "PolylineDashMaterialProperty" in js


class TestPolylineOutlineMaterial:
    def test_to_js(self):
        m = PolylineOutlineMaterial(color=WHITE, outline_color=RED, outline_width=2.0)
        js = m.to_js()
        assert "PolylineOutlineMaterialProperty" in js
