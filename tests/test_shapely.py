"""Tests for shapely geometry conversion helpers."""

import pytest

pytest.importorskip("shapely")

from shapely.geometry import (  # noqa: E402
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from cesiumkit import Cartesian3, Entity, PolygonGraphics, PolylineGraphics  # noqa: E402
from cesiumkit._shapely import (  # noqa: E402
    is_shapely_geom,
    shapely_line_to_positions,
    shapely_point_to_cartesian3,
    shapely_polygon_to_hierarchy,
    shapely_to_entities,
)
from cesiumkit.coordinates import Cartesian3FromDegrees  # noqa: E402
from cesiumkit.entities.polygon import PolygonHierarchy  # noqa: E402


class TestIsShapelyGeom:
    def test_detects_point(self):
        assert is_shapely_geom(Point(1, 2))

    def test_detects_polygon(self):
        assert is_shapely_geom(Polygon([(0, 0), (1, 0), (1, 1)]))

    def test_rejects_plain_dict(self):
        assert not is_shapely_geom({"type": "Point", "coordinates": [0, 0]})

    def test_rejects_list(self):
        assert not is_shapely_geom([1, 2, 3])

    def test_rejects_none(self):
        assert not is_shapely_geom(None)


class TestShapelyPointToCartesian3:
    def test_2d_point(self):
        c = shapely_point_to_cartesian3(Point(-74.006, 40.7128))
        assert isinstance(c, Cartesian3FromDegrees)
        assert c.longitude == -74.006
        assert c.latitude == 40.7128
        assert c.height == 0.0

    def test_3d_point(self):
        c = shapely_point_to_cartesian3(Point(-74.006, 40.7128, 500))
        assert c.height == 500.0


class TestShapelyLineToPositions:
    def test_linestring(self):
        line = LineString([(0, 0), (1, 1), (2, 2)])
        positions = shapely_line_to_positions(line)
        assert len(positions) == 3
        assert all(isinstance(p, Cartesian3FromDegrees) for p in positions)
        assert positions[0].longitude == 0
        assert positions[2].latitude == 2

    def test_linearring(self):
        ring = LinearRing([(0, 0), (1, 0), (1, 1), (0, 1)])
        positions = shapely_line_to_positions(ring)
        # LinearRing closes itself, so 4 unique -> 5 coords
        assert len(positions) == 5

    def test_3d_linestring(self):
        line = LineString([(0, 0, 10), (1, 1, 20)])
        positions = shapely_line_to_positions(line)
        assert positions[0].height == 10.0
        assert positions[1].height == 20.0


class TestShapelyPolygonToHierarchy:
    def test_simple_polygon(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        hierarchy = shapely_polygon_to_hierarchy(poly)
        assert isinstance(hierarchy, PolygonHierarchy)
        assert hierarchy.holes is None
        assert len(hierarchy.positions) == 5  # shapely closes the ring

    def test_polygon_with_hole(self):
        exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
        hole = [(2, 2), (4, 2), (4, 4), (2, 4)]
        poly = Polygon(exterior, [hole])
        hierarchy = shapely_polygon_to_hierarchy(poly)
        assert hierarchy.holes is not None
        assert len(hierarchy.holes) == 1
        assert len(hierarchy.holes[0].positions) == 5

    def test_polygon_with_multiple_holes(self):
        exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
        hole1 = [(2, 2), (3, 2), (3, 3), (2, 3)]
        hole2 = [(6, 6), (7, 6), (7, 7), (6, 7)]
        poly = Polygon(exterior, [hole1, hole2])
        hierarchy = shapely_polygon_to_hierarchy(poly)
        assert len(hierarchy.holes) == 2


class TestShapelyToEntities:
    def test_point(self):
        entities = shapely_to_entities(Point(1, 2), name="P")
        assert len(entities) == 1
        assert entities[0].name == "P"
        assert entities[0].position is not None
        assert entities[0].point is not None

    def test_linestring(self):
        entities = shapely_to_entities(LineString([(0, 0), (1, 1)]))
        assert len(entities) == 1
        assert entities[0].polyline is not None

    def test_polygon(self):
        entities = shapely_to_entities(Polygon([(0, 0), (1, 0), (1, 1)]))
        assert len(entities) == 1
        assert entities[0].polygon is not None

    def test_multipoint(self):
        mp = MultiPoint([(0, 0), (1, 1), (2, 2)])
        entities = shapely_to_entities(mp)
        assert len(entities) == 3

    def test_multilinestring(self):
        ml = MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]])
        entities = shapely_to_entities(ml)
        assert len(entities) == 2

    def test_multipolygon(self):
        mp = MultiPolygon(
            [
                Polygon([(0, 0), (1, 0), (1, 1)]),
                Polygon([(5, 5), (6, 5), (6, 6)]),
            ]
        )
        entities = shapely_to_entities(mp)
        assert len(entities) == 2

    def test_geometry_collection(self):
        gc = GeometryCollection([Point(0, 0), LineString([(1, 1), (2, 2)])])
        entities = shapely_to_entities(gc)
        assert len(entities) == 2

    def test_unsupported_raises(self):
        class Fake:
            geom_type = "Unknown"
            __geo_interface__ = {}

        with pytest.raises(ValueError, match="Unsupported"):
            shapely_to_entities(Fake())


class TestCartesian3FromShapely:
    def test_from_point(self):
        c = Cartesian3.from_shapely(Point(10, 20))
        assert isinstance(c, Cartesian3FromDegrees)
        assert c.longitude == 10

    def test_non_shapely_raises(self):
        with pytest.raises(ValueError, match="shapely"):
            Cartesian3.from_shapely([1, 2])

    def test_non_point_raises(self):
        with pytest.raises(ValueError, match="Point"):
            Cartesian3.from_shapely(LineString([(0, 0), (1, 1)]))


class TestEntityValidator:
    def test_entity_accepts_shapely_point(self):
        e = Entity(name="NYC", position=Point(-74.006, 40.7128))
        assert isinstance(e.position, Cartesian3FromDegrees)
        assert e.position.longitude == -74.006

    def test_entity_preserves_existing_position(self):
        cart = Cartesian3.from_degrees(1, 2, 3)
        e = Entity(position=cart)
        assert e.position is cart


class TestPolygonGraphicsValidator:
    def test_hierarchy_accepts_shapely_polygon(self):
        g = PolygonGraphics(hierarchy=Polygon([(0, 0), (1, 0), (1, 1)]))
        assert isinstance(g.hierarchy, PolygonHierarchy)

    def test_hierarchy_preserves_list(self):
        positions = [Cartesian3.from_degrees(0, 0), Cartesian3.from_degrees(1, 0)]
        g = PolygonGraphics(hierarchy=positions)
        assert g.hierarchy == positions


class TestPolylineGraphicsValidator:
    def test_positions_accepts_shapely_linestring(self):
        g = PolylineGraphics(positions=LineString([(0, 0), (1, 1), (2, 2)]))
        assert isinstance(g.positions, list)
        assert len(g.positions) == 3
        assert all(isinstance(p, Cartesian3FromDegrees) for p in g.positions)

    def test_positions_accepts_linearring(self):
        g = PolylineGraphics(positions=LinearRing([(0, 0), (1, 0), (1, 1)]))
        assert isinstance(g.positions, list)
        assert len(g.positions) == 4  # closed

    def test_positions_preserves_list(self):
        positions = [Cartesian3.from_degrees(0, 0), Cartesian3.from_degrees(1, 1)]
        g = PolylineGraphics(positions=positions)
        assert g.positions == positions


class TestEndToEnd:
    def test_polygon_entity_from_shapely_renders_js(self):
        e = Entity(
            name="Square",
            polygon=PolygonGraphics(hierarchy=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])),
        )
        js = e.to_js()
        assert "PolygonHierarchy" in js

    def test_polyline_entity_from_shapely_renders_js(self):
        e = Entity(
            name="Path",
            polyline=PolylineGraphics(positions=LineString([(0, 0), (1, 1)]), width=3),
        )
        js = e.to_js()
        assert "fromDegrees" in js
