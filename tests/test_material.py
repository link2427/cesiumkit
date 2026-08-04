"""Tests for cesiumkit.material module."""

import pytest

from cesiumkit.color import BLUE, RED, WHITE
from cesiumkit.coordinates import Cartesian2
from cesiumkit.enums import StripeOrientation
from cesiumkit.material import (
    CheckerboardMaterial,
    GridMaterial,
    ImageMaterial,
    MaterialBase,
    PolylineArrowMaterial,
    PolylineDashMaterial,
    PolylineGlowMaterial,
    PolylineOutlineMaterial,
    SolidColorMaterial,
    StripeMaterial,
)


class TestMaterialBase:
    def test_js_class_name_not_implemented(self):
        with pytest.raises(NotImplementedError):
            MaterialBase()._js_class_name()


class TestSolidColorMaterial:
    def test_to_js(self):
        m = SolidColorMaterial(color=RED)
        js = m.to_js()
        assert "Cesium.Color.RED" in js

    def test_to_js_with_raw_color(self):
        m = SolidColorMaterial(color="#ff0000")
        assert m.to_js() == '"#ff0000"'

    def test_to_js_without_color(self):
        assert SolidColorMaterial().to_js() == "undefined"

    def test_to_czml(self):
        m = SolidColorMaterial(color=RED)
        assert m.to_czml() == {"solidColor": {"color": RED.to_czml()}}

    def test_to_czml_without_color(self):
        assert SolidColorMaterial().to_czml() == {}


class TestImageMaterial:
    def test_to_js(self):
        m = ImageMaterial(image="https://example.com/texture.png")
        js = m.to_js()
        assert "ImageMaterialProperty" in js
        assert "example.com/texture.png" in js

    def test_to_js_empty(self):
        assert ImageMaterial().to_js() == "new Cesium.ImageMaterialProperty()"

    def test_to_js_all_fields(self):
        m = ImageMaterial(
            image="tex.png",
            repeat=Cartesian2(x=2, y=2),
            color=RED,
            transparent=True,
        )
        js = m.to_js()
        assert '"tex.png"' in js
        assert "new Cesium.Cartesian2(2.0, 2.0)" in js
        assert "Cesium.Color.RED" in js
        assert "transparent: true" in js

    def test_to_czml(self):
        m = ImageMaterial(
            image="tex.png",
            repeat=Cartesian2(x=2, y=2),
            color=RED,
            transparent=True,
        )
        assert m.to_czml() == {
            "image": {
                "image": "tex.png",
                "repeat": Cartesian2(x=2, y=2).to_czml(),
                "color": RED.to_czml(),
                "transparent": True,
            }
        }

    def test_to_czml_empty(self):
        assert ImageMaterial().to_czml() == {}


class TestGridMaterial:
    def test_to_js(self):
        m = GridMaterial(color=WHITE)
        js = m.to_js()
        assert "GridMaterialProperty" in js

    def test_to_czml(self):
        m = GridMaterial(
            color=RED,
            cell_alpha=0.5,
            line_count=Cartesian2(x=8, y=8),
            line_thickness=Cartesian2(x=1, y=1),
            line_offset=Cartesian2(x=0, y=0),
        )
        assert m.to_czml() == {
            "grid": {
                "color": RED.to_czml(),
                "cellAlpha": 0.5,
                "lineCount": Cartesian2(x=8, y=8).to_czml(),
                "lineThickness": Cartesian2(x=1, y=1).to_czml(),
                "lineOffset": Cartesian2(x=0, y=0).to_czml(),
            }
        }

    def test_to_czml_empty(self):
        assert GridMaterial().to_czml() == {}


class TestStripeMaterial:
    def test_to_js(self):
        m = StripeMaterial(even_color=RED, odd_color=BLUE, repeat=5.0)
        js = m.to_js()
        assert "StripeMaterialProperty" in js
        assert "Cesium.Color.RED" in js
        assert "Cesium.Color.BLUE" in js

    def test_to_czml(self):
        m = StripeMaterial(
            orientation=StripeOrientation.HORIZONTAL,
            even_color=RED,
            odd_color=BLUE,
            offset=0.5,
            repeat=5.0,
        )
        result = m.to_czml()
        assert result["stripe"]["orientation"] == str(StripeOrientation.HORIZONTAL)
        assert result["stripe"]["evenColor"] == RED.to_czml()
        assert result["stripe"]["oddColor"] == BLUE.to_czml()
        assert result["stripe"]["offset"] == 0.5
        assert result["stripe"]["repeat"] == 5.0

    def test_to_czml_empty(self):
        assert StripeMaterial().to_czml() == {}


class TestCheckerboardMaterial:
    def test_to_js(self):
        m = CheckerboardMaterial(even_color=WHITE, odd_color=BLUE, repeat=Cartesian2(x=4, y=4))
        js = m.to_js()
        assert "CheckerboardMaterialProperty" in js
        assert "Cesium.Color.WHITE" in js
        assert "new Cesium.Cartesian2(4.0, 4.0)" in js

    def test_to_czml(self):
        m = CheckerboardMaterial(even_color=WHITE, odd_color=BLUE, repeat=Cartesian2(x=4, y=4))
        assert m.to_czml() == {
            "checkerboard": {
                "evenColor": WHITE.to_czml(),
                "oddColor": BLUE.to_czml(),
                "repeat": Cartesian2(x=4, y=4).to_czml(),
            }
        }

    def test_to_czml_empty(self):
        assert CheckerboardMaterial().to_czml() == {}


class TestPolylineGlowMaterial:
    def test_to_js(self):
        m = PolylineGlowMaterial(color=RED, glow_power=0.2)
        js = m.to_js()
        assert "PolylineGlowMaterialProperty" in js
        assert "0.2" in js

    def test_to_czml(self):
        m = PolylineGlowMaterial(color=RED, glow_power=0.2, taper_power=0.5)
        assert m.to_czml() == {"polylineGlow": {"color": RED.to_czml(), "glowPower": 0.2, "taperPower": 0.5}}

    def test_to_czml_empty(self):
        assert PolylineGlowMaterial().to_czml() == {}


class TestPolylineArrowMaterial:
    def test_to_js(self):
        m = PolylineArrowMaterial(color=RED)
        js = m.to_js()
        assert "PolylineArrowMaterialProperty" in js

    def test_to_czml(self):
        m = PolylineArrowMaterial(color=RED)
        assert m.to_czml() == {"polylineArrow": {"color": RED.to_czml()}}

    def test_to_czml_empty(self):
        assert PolylineArrowMaterial().to_czml() == {}


class TestPolylineDashMaterial:
    def test_to_js(self):
        m = PolylineDashMaterial(color=RED, dash_length=16.0)
        js = m.to_js()
        assert "PolylineDashMaterialProperty" in js

    def test_to_czml(self):
        m = PolylineDashMaterial(color=RED, gap_color=BLUE, dash_length=16.0, dash_pattern=255)
        assert m.to_czml() == {
            "polylineDash": {
                "color": RED.to_czml(),
                "gapColor": BLUE.to_czml(),
                "dashLength": 16.0,
                "dashPattern": 255,
            }
        }

    def test_to_czml_empty(self):
        assert PolylineDashMaterial().to_czml() == {}


class TestPolylineOutlineMaterial:
    def test_to_js(self):
        m = PolylineOutlineMaterial(color=WHITE, outline_color=RED, outline_width=2.0)
        js = m.to_js()
        assert "PolylineOutlineMaterialProperty" in js

    def test_to_czml(self):
        m = PolylineOutlineMaterial(color=WHITE, outline_color=RED, outline_width=2.0)
        assert m.to_czml() == {
            "polylineOutline": {
                "color": WHITE.to_czml(),
                "outlineColor": RED.to_czml(),
                "outlineWidth": 2.0,
            }
        }

    def test_to_czml_empty(self):
        assert PolylineOutlineMaterial().to_czml() == {}
