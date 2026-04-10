"""Tests for GeoPandas / pandas integration in cesiumkit.gis."""

import pytest

pytest.importorskip("geopandas")
pytest.importorskip("shapely")

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402
from shapely.geometry import LineString, MultiPoint, Point, Polygon  # noqa: E402

from cesiumkit import (  # noqa: E402
    Color,
    Entity,
    Viewer,
    dataframe_to_entities,
    geodataframe_to_entities,
)
from cesiumkit.coordinates import Cartesian3FromDegrees  # noqa: E402
from cesiumkit.entities.polygon import PolygonHierarchy  # noqa: E402


def _mixed_gdf():
    """Small synthetic GeoDataFrame with mixed geometry types."""
    return gpd.GeoDataFrame(
        {
            "name": ["A", "B", "C"],
            "pop": [100, 200, 300],
            "color": ["#ff0000", "#00ff00", "#0000ff"],
            "height_m": [10.0, 20.0, 30.0],
            "geometry": [
                Point(-74.0, 40.7),
                LineString([(0, 0), (1, 1), (2, 2)]),
                Polygon([(5, 5), (6, 5), (6, 6), (5, 6)]),
            ],
        },
        crs="EPSG:4326",
    )


class TestGeodataframeToEntitiesBasic:
    def test_returns_list_of_entities(self):
        entities = geodataframe_to_entities(_mixed_gdf())
        assert len(entities) == 3
        assert all(isinstance(e, Entity) for e in entities)

    def test_point_has_position(self):
        entities = geodataframe_to_entities(_mixed_gdf())
        point_entity = entities[0]
        assert isinstance(point_entity.position, Cartesian3FromDegrees)
        assert point_entity.point is not None

    def test_linestring_has_polyline(self):
        entities = geodataframe_to_entities(_mixed_gdf())
        line_entity = entities[1]
        assert line_entity.polyline is not None
        assert len(line_entity.polyline.positions) == 3

    def test_polygon_has_hierarchy(self):
        entities = geodataframe_to_entities(_mixed_gdf())
        poly_entity = entities[2]
        assert poly_entity.polygon is not None
        assert isinstance(poly_entity.polygon.hierarchy, PolygonHierarchy)


class TestColumnMapping:
    def test_name_column(self):
        entities = geodataframe_to_entities(_mixed_gdf(), name_column="name")
        assert [e.name for e in entities] == ["A", "B", "C"]

    def test_name_missing_column_ignored(self):
        entities = geodataframe_to_entities(_mixed_gdf(), name_column="nonexistent")
        assert all(e.name is None for e in entities)

    def test_description_column(self):
        gdf = _mixed_gdf()
        gdf["info"] = ["info-A", "info-B", "info-C"]
        entities = geodataframe_to_entities(gdf, description_column="info")
        assert entities[0].description == "info-A"


class TestColorHandling:
    def test_single_color_instance(self):
        entities = geodataframe_to_entities(_mixed_gdf(), color=Color.RED)
        assert entities[0].point.color is not None

    def test_single_color_named_string(self):
        entities = geodataframe_to_entities(_mixed_gdf(), color="RED")
        assert entities[0].point.color is not None

    def test_single_color_css_string(self):
        entities = geodataframe_to_entities(_mixed_gdf(), color="#ff8800")
        assert entities[0].point.color is not None

    def test_color_column(self):
        entities = geodataframe_to_entities(_mixed_gdf(), color_column="color")
        # Each point gets a different color from the column
        colors = [e.point.color for e in entities if e.point is not None]
        assert len(colors) == 1  # only one Point in the mixed gdf
        assert colors[0].red == 1.0  # #ff0000

    def test_polygon_fill_alpha(self):
        entities = geodataframe_to_entities(_mixed_gdf(), color=Color.BLUE, fill_alpha=0.3)
        poly = entities[2]
        assert poly.polygon.material is not None
        assert poly.polygon.material.alpha == 0.3


class TestHeightExtrusion:
    def test_height_column_on_polygon(self):
        gdf = _mixed_gdf()
        entities = geodataframe_to_entities(gdf, height_column="height_m")
        poly = entities[2]
        assert poly.polygon.height == 30.0

    def test_extruded_height_column(self):
        gdf = _mixed_gdf()
        gdf["ext"] = [0, 0, 500]
        entities = geodataframe_to_entities(gdf, extruded_height_column="ext")
        poly = entities[2]
        assert poly.polygon.extruded_height == 500.0


class TestCRSReprojection:
    def test_non_wgs84_is_reprojected(self):
        # EPSG:3857 (Web Mercator). 0,0 is still origin, so we pick a non-origin point.
        gdf = gpd.GeoDataFrame(
            {"name": ["P"], "geometry": [Point(100000, 200000)]},
            crs="EPSG:3857",
        )
        entities = geodataframe_to_entities(gdf, name_column="name")
        pos = entities[0].position
        # Web Mercator (100000, 200000) is approximately (0.898, 1.793) in lon/lat
        assert abs(pos.longitude - 0.898) < 0.1
        assert abs(pos.latitude - 1.793) < 0.1

    def test_no_crs_is_left_alone(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["P"], "geometry": [Point(-74, 40.7)]},
        )
        # Should not crash
        entities = geodataframe_to_entities(gdf, name_column="name")
        assert entities[0].position.longitude == -74


class TestMultiGeometry:
    def test_multipoint_yields_multiple_entities(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["cluster"], "geometry": [MultiPoint([(0, 0), (1, 1), (2, 2)])]},
            crs="EPSG:4326",
        )
        entities = geodataframe_to_entities(gdf, name_column="name")
        assert len(entities) == 3


class TestEmptyAndNone:
    def test_none_geometry_skipped(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"], "geometry": [Point(0, 0), None]},
            crs="EPSG:4326",
        )
        entities = geodataframe_to_entities(gdf, name_column="name")
        assert len(entities) == 1

    def test_empty_gdf(self):
        gdf = gpd.GeoDataFrame({"name": [], "geometry": []}, crs="EPSG:4326")
        entities = geodataframe_to_entities(gdf)
        assert entities == []


class TestDataframeToEntities:
    def test_basic_lon_lat(self):
        df = pd.DataFrame(
            {
                "city": ["NYC", "LA"],
                "lon": [-74.006, -118.243],
                "lat": [40.7128, 34.0522],
            }
        )
        entities = dataframe_to_entities(df, "lon", "lat", name_column="city")
        assert len(entities) == 2
        assert entities[0].name == "NYC"
        assert entities[0].position.longitude == -74.006

    def test_with_height(self):
        df = pd.DataFrame({"lon": [0], "lat": [0], "alt": [500]})
        entities = dataframe_to_entities(df, "lon", "lat", height_col="alt")
        assert entities[0].position.height == 500.0

    def test_color(self):
        df = pd.DataFrame({"lon": [0], "lat": [0]})
        entities = dataframe_to_entities(df, "lon", "lat", color=Color.GREEN)
        assert entities[0].point.color is not None


class TestViewerIntegration:
    def test_add_geodataframe(self):
        v = Viewer()
        result = v.add_geodataframe(_mixed_gdf(), name_column="name")
        assert len(result) == 3
        assert len(v.entities) == 3

    def test_add_dataframe(self):
        v = Viewer()
        df = pd.DataFrame({"lon": [0, 1], "lat": [0, 1]})
        result = v.add_dataframe(df, "lon", "lat")
        assert len(result) == 2
        assert len(v.entities) == 2

    def test_viewer_renders_html_after_add_geodataframe(self):
        v = Viewer()
        v.add_geodataframe(_mixed_gdf(), name_column="name", color=Color.RED)
        html = v.to_html()
        assert "PolygonHierarchy" in html
        assert "fromDegrees" in html
