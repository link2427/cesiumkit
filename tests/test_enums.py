"""Tests for cesiumkit.enums module."""

from cesiumkit.enums import (
    ArcType,
    ClockRange,
    HeightReference,
    SceneMode,
    ScreenSpaceEventType,
    ShadowMode,
)


class TestEnums:
    def test_height_reference_to_js(self):
        assert HeightReference.CLAMP_TO_GROUND.to_js() == "Cesium.HeightReference.CLAMP_TO_GROUND"

    def test_scene_mode_to_js(self):
        assert SceneMode.SCENE3D.to_js() == "Cesium.SceneMode.SCENE3D"
        assert SceneMode.SCENE2D.to_js() == "Cesium.SceneMode.SCENE2D"
        assert SceneMode.COLUMBUS_VIEW.to_js() == "Cesium.SceneMode.COLUMBUS_VIEW"

    def test_shadow_mode_to_js(self):
        assert ShadowMode.ENABLED.to_js() == "Cesium.ShadowMode.ENABLED"

    def test_arc_type_to_js(self):
        assert ArcType.GEODESIC.to_js() == "Cesium.ArcType.GEODESIC"

    def test_clock_range_to_js(self):
        assert ClockRange.LOOP_STOP.to_js() == "Cesium.ClockRange.LOOP_STOP"

    def test_screen_space_event(self):
        assert ScreenSpaceEventType.LEFT_CLICK.to_js() == "Cesium.ScreenSpaceEventType.LEFT_CLICK"
