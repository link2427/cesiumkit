"""Tests for cesiumkit entity system."""

from cesiumkit.color import RED
from cesiumkit.coordinates import Cartesian3, RectangleCoords
from cesiumkit.entities._base import Entity, EntityCollection
from cesiumkit.entities.billboard import BillboardGraphics
from cesiumkit.entities.box import BoxGraphics
from cesiumkit.entities.corridor import CorridorGraphics
from cesiumkit.entities.cylinder import CylinderGraphics
from cesiumkit.entities.ellipse import EllipseGraphics
from cesiumkit.entities.ellipsoid import EllipsoidGraphics
from cesiumkit.entities.label import LabelGraphics
from cesiumkit.entities.model import ModelGraphics
from cesiumkit.entities.path import PathGraphics
from cesiumkit.entities.point import PointGraphics
from cesiumkit.entities.polygon import PolygonGraphics, PolygonHierarchy
from cesiumkit.entities.polyline import PolylineGraphics
from cesiumkit.entities.rectangle import RectangleGraphics
from cesiumkit.entities.wall import WallGraphics


class TestPointGraphics:
    def test_to_js(self):
        p = PointGraphics(pixel_size=10, color=RED)
        js = p.to_js()
        assert "pixelSize" in js
        assert "10" in js
        assert "Cesium.Color.RED" in js

    def test_graphics_key(self):
        assert PointGraphics()._graphics_key() == "point"


class TestLabelGraphics:
    def test_to_js(self):
        label = LabelGraphics(text="Hello", font="16px sans-serif")
        js = label.to_js()
        assert "Hello" in js
        assert "font" in js


class TestBillboardGraphics:
    def test_to_js(self):
        b = BillboardGraphics(image="marker.png", scale=2.0)
        js = b.to_js()
        assert "marker.png" in js
        assert "scale" in js


class TestPolygonGraphics:
    def test_with_list_hierarchy(self):
        p = PolygonGraphics(
            hierarchy=[
                Cartesian3.from_degrees(-115, 37),
                Cartesian3.from_degrees(-115, 32),
                Cartesian3.from_degrees(-107, 33),
            ],
            material=RED,
        )
        js = p.to_js()
        assert "hierarchy" in js or "PolygonHierarchy" in js
        assert "fromDegrees" in js

    def test_with_polygon_hierarchy(self):
        h = PolygonHierarchy(
            positions=[
                Cartesian3.from_degrees(-115, 37),
                Cartesian3.from_degrees(-115, 32),
            ]
        )
        js = h.to_js()
        assert "PolygonHierarchy" in js


class TestPolylineGraphics:
    def test_to_js(self):
        p = PolylineGraphics(
            positions=[
                Cartesian3.from_degrees(-75, 35),
                Cartesian3.from_degrees(-125, 35),
            ],
            width=5,
        )
        js = p.to_js()
        assert "positions" in js
        assert "width" in js


class TestBoxGraphics:
    def test_to_js(self):
        b = BoxGraphics(dimensions=Cartesian3(x=100, y=200, z=300))
        js = b.to_js()
        assert "dimensions" in js


class TestCylinderGraphics:
    def test_to_js(self):
        c = CylinderGraphics(length=100, top_radius=10, bottom_radius=20)
        js = c.to_js()
        assert "length" in js
        assert "topRadius" in js
        assert "bottomRadius" in js


class TestEllipseGraphics:
    def test_to_js(self):
        e = EllipseGraphics(semi_major_axis=300000, semi_minor_axis=200000)
        js = e.to_js()
        assert "semiMajorAxis" in js
        assert "semiMinorAxis" in js


class TestEllipsoidGraphics:
    def test_to_js(self):
        e = EllipsoidGraphics(radii=Cartesian3(x=100, y=100, z=200))
        js = e.to_js()
        assert "radii" in js


class TestModelGraphics:
    def test_to_js(self):
        m = ModelGraphics(uri="model.glb", scale=2.0)
        js = m.to_js()
        assert "model.glb" in js
        assert "scale" in js


class TestCorridorGraphics:
    def test_to_js(self):
        c = CorridorGraphics(
            positions=[Cartesian3.from_degrees(-75, 35), Cartesian3.from_degrees(-125, 35)],
            width=100000,
        )
        js = c.to_js()
        assert "positions" in js
        assert "width" in js


class TestWallGraphics:
    def test_to_js(self):
        w = WallGraphics(
            positions=[Cartesian3.from_degrees(-75, 35), Cartesian3.from_degrees(-80, 35)],
        )
        js = w.to_js()
        assert "positions" in js


class TestRectangleGraphics:
    def test_to_js(self):
        r = RectangleGraphics(
            coordinates=RectangleCoords.from_degrees(-120, 30, -80, 50),
        )
        js = r.to_js()
        assert "coordinates" in js


class TestPathGraphics:
    def test_to_js(self):
        p = PathGraphics(width=2, trail_time=3600)
        js = p.to_js()
        assert "width" in js
        assert "trailTime" in js


class TestEntity:
    def test_basic_entity_to_js(self):
        e = Entity(
            name="Test",
            position=Cartesian3.from_degrees(-75, 40, 100),
            point=PointGraphics(pixel_size=10, color=RED),
        )
        js = e.to_js()
        assert '"Test"' in js
        assert "fromDegrees" in js
        assert "pixelSize" in js

    def test_entity_with_multiple_graphics(self):
        e = Entity(
            name="Multi",
            position=Cartesian3.from_degrees(-75, 40),
            point=PointGraphics(pixel_size=10),
            label=LabelGraphics(text="Hello"),
        )
        js = e.to_js()
        assert "point" in js
        assert "label" in js

    def test_entity_czml_packet(self):
        e = Entity(
            id="test-entity",
            name="Test",
            position=Cartesian3.from_degrees(-75, 40, 100),
        )
        pkt = e.to_czml_packet()
        assert pkt["id"] == "test-entity"
        assert pkt["name"] == "Test"


class TestEntityCollection:
    def test_add_entity(self):
        ec = EntityCollection()
        e = ec.add(Entity(name="Test"))
        assert len(ec) == 1
        assert e.name == "Test"

    def test_add_kwargs(self):
        ec = EntityCollection()
        e = ec.add(name="Test2")
        assert len(ec) == 1
        assert e.name == "Test2"

    def test_remove(self):
        ec = EntityCollection()
        e = ec.add(Entity(name="Test"))
        assert ec.remove(e) is True
        assert len(ec) == 0

    def test_remove_all(self):
        ec = EntityCollection()
        ec.add(Entity(name="A"))
        ec.add(Entity(name="B"))
        ec.remove_all()
        assert len(ec) == 0

    def test_get_by_id(self):
        ec = EntityCollection()
        ec.add(Entity(id="abc", name="Found"))
        result = ec.get_by_id("abc")
        assert result is not None
        assert result.name == "Found"

    def test_iteration(self):
        ec = EntityCollection()
        ec.add(Entity(name="A"))
        ec.add(Entity(name="B"))
        names = [e.name for e in ec]
        assert names == ["A", "B"]
