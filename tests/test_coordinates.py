"""Tests for cesiumkit.coordinates module."""

from cesiumkit.coordinates import (
    Cartesian2,
    Cartesian3,
    Cartographic,
    RectangleCoords,
    NearFarScalar,
    DistanceDisplayCondition,
    BoundingSphere,
)


class TestCartesian2:
    def test_to_js(self):
        c = Cartesian2(x=10, y=20)
        assert c.to_js() == "new Cesium.Cartesian2(10.0, 20.0)"


class TestCartesian3:
    def test_to_js(self):
        c = Cartesian3(x=1.0, y=2.0, z=3.0)
        assert c.to_js() == "new Cesium.Cartesian3(1.0, 2.0, 3.0)"

    def test_from_degrees(self):
        c = Cartesian3.from_degrees(-75.0, 40.0, 100.0)
        assert "fromDegrees" in c.to_js()
        assert "-75.0" in c.to_js()
        assert "40.0" in c.to_js()
        assert "100.0" in c.to_js()

    def test_from_degrees_no_height(self):
        c = Cartesian3.from_degrees(-75.0, 40.0)
        js = c.to_js()
        assert js == "Cesium.Cartesian3.fromDegrees(-75.0, 40.0)"

    def test_from_radians(self):
        c = Cartesian3.from_radians(1.0, 0.5, 100.0)
        assert "fromRadians" in c.to_js()

    def test_from_degrees_array(self):
        c = Cartesian3.from_degrees_array([-75, 40, -80, 35])
        assert "fromDegreesArray" in c.to_js()

    def test_from_degrees_array_heights(self):
        c = Cartesian3.from_degrees_array_heights([-75, 40, 100, -80, 35, 200])
        assert "fromDegreesArrayHeights" in c.to_js()

    def test_czml_cartesian(self):
        c = Cartesian3(x=1.0, y=2.0, z=3.0)
        assert c.to_czml() == {"cartesian": [1.0, 2.0, 3.0]}

    def test_czml_degrees(self):
        c = Cartesian3.from_degrees(-75.0, 40.0, 100.0)
        assert c.to_czml() == {"cartographicDegrees": [-75.0, 40.0, 100.0]}


class TestCartographic:
    def test_to_js(self):
        c = Cartographic(longitude=1.0, latitude=0.5, height=100.0)
        assert "new Cesium.Cartographic" in c.to_js()

    def test_from_degrees(self):
        c = Cartographic.from_degrees(-75.0, 40.0, 100.0)
        assert "fromDegrees" in c.to_js()


class TestRectangleCoords:
    def test_to_js(self):
        r = RectangleCoords(west=-2.0, south=0.5, east=-1.0, north=1.0)
        assert "new Cesium.Rectangle" in r.to_js()

    def test_from_degrees(self):
        r = RectangleCoords.from_degrees(-120, 30, -80, 50)
        assert "fromDegrees" in r.to_js()


class TestNearFarScalar:
    def test_to_js(self):
        nfs = NearFarScalar(near=1e2, near_value=1.0, far=1e7, far_value=0.0)
        js = nfs.to_js()
        assert "NearFarScalar" in js


class TestDistanceDisplayCondition:
    def test_to_js(self):
        ddc = DistanceDisplayCondition(near=0, far=1e7)
        assert "DistanceDisplayCondition" in ddc.to_js()


class TestBoundingSphere:
    def test_to_js(self):
        bs = BoundingSphere(center=Cartesian3(x=0, y=0, z=0), radius=100)
        assert "BoundingSphere" in bs.to_js()
