"""Tests for cesiumkit.camera module."""

from cesiumkit.camera import Camera
from cesiumkit.coordinates import Cartesian3
from cesiumkit.math import HeadingPitchRoll, HeadingPitchRange


class TestCamera:
    def test_fly_to(self):
        cam = Camera()
        cam.fly_to(Cartesian3.from_degrees(-75, 40, 15000), duration=3.0)
        ops = cam.to_js_operations("viewer")
        assert len(ops) == 1
        assert "camera.flyTo" in ops[0]
        assert "fromDegrees" in ops[0]

    def test_set_view(self):
        cam = Camera()
        cam.set_view(Cartesian3.from_degrees(-75, 40, 15000))
        ops = cam.to_js_operations("viewer")
        assert len(ops) == 1
        assert "camera.setView" in ops[0]

    def test_look_at(self):
        cam = Camera()
        cam.look_at(
            Cartesian3.from_degrees(-75, 40, 0),
            HeadingPitchRange(heading=0, pitch=-0.5, range=15000),
        )
        ops = cam.to_js_operations("viewer")
        assert len(ops) == 1
        assert "camera.lookAt" in ops[0]

    def test_zoom_in(self):
        cam = Camera()
        cam.zoom_in(500)
        ops = cam.to_js_operations("viewer")
        assert "zoomIn(500)" in ops[0]

    def test_zoom_out_no_amount(self):
        cam = Camera()
        cam.zoom_out()
        ops = cam.to_js_operations("viewer")
        assert "zoomOut()" in ops[0]

    def test_chaining(self):
        cam = Camera()
        cam.fly_to(Cartesian3.from_degrees(-75, 40, 15000)).zoom_in(100)
        ops = cam.to_js_operations("viewer")
        assert len(ops) == 2

    def test_multiple_operations(self):
        cam = Camera()
        cam.set_view(Cartesian3.from_degrees(-75, 40, 15000))
        cam.fly_to(Cartesian3.from_degrees(-80, 35, 10000))
        ops = cam.to_js_operations("viewer")
        assert len(ops) == 2
        assert "setView" in ops[0]
        assert "flyTo" in ops[1]
