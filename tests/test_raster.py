"""Tests for local raster tile serving (requires the [raster] extras)."""

import io
from pathlib import Path

import pytest

pytest.importorskip("rio_tiler")
pytest.importorskip("rasterio")
pytest.importorskip("xarray")

import rasterio  # noqa: E402
from rasterio.transform import from_bounds  # noqa: E402

import cesiumkit  # noqa: E402
from cesiumkit.raster import RasterSource  # noqa: E402
from tests.test_offline import OfflineServer  # noqa: E402


@pytest.fixture()
def bounded_tif(tmp_path):
    """A small GeoTIFF covering lon/lat -10..10 with a single red pixel."""
    import numpy as np

    path = tmp_path / "bounded.tif"
    pixels = np.zeros((3, 2, 4), dtype="uint8")
    pixels[0, ...] = 255  # red band
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=4,
        count=3,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_bounds(-10, -10, 10, 10, 4, 2),
    ) as dst:
        dst.write(pixels)
    return str(path)


class TestRasterSource:
    def test_tile_returns_png(self, bounded_tif):
        source = RasterSource(bounded_tif)
        body = source.tile(0, 0, 0)
        assert body is not None
        assert body[:8] == b"\x89PNG\r\n\x1a\n"

    def test_out_of_range_tile_returns_none(self, bounded_tif):
        source = RasterSource(bounded_tif)
        # z=12 tile (0,0) is the far northwest corner of the world, well
        # outside the raster's -10..10 extent.
        assert source.tile(12, 0, 0) is None

    def test_repeated_tile_is_cached(self, bounded_tif):
        source = RasterSource(bounded_tif)
        first = source.tile(0, 0, 0)
        second = source.tile(0, 0, 0)
        assert first == second
        assert source.cached_tiles == 1

    def test_cache_evicts_least_recently_used(self, bounded_tif):
        source = RasterSource(bounded_tif, tile_cache_size=2)
        source.tile(0, 0, 0)
        # Out-of-range tiles are not cached.
        assert source.tile(12, 0, 0) is None
        assert source.cached_tiles == 1
        # Fill past the limit; a fresh miss must evict the least recently
        # used entries (the manually inserted ones), keeping the touched one.
        source._tile_cache[(9, 9, 9)] = b"old"
        source._tile_cache[(9, 9, 10)] = b"new"
        assert source.cached_tiles == 3
        source.tile(0, 0, 0)  # LRU touch: (0, 0, 0) becomes most recent
        source.tile(1, 0, 1)  # miss: inserts and evicts down to the limit
        assert source.cached_tiles == 2
        assert (0, 0, 0) in source._tile_cache
        assert (1, 0, 1) in source._tile_cache
        assert (9, 9, 9) not in source._tile_cache
        assert (9, 9, 10) not in source._tile_cache

    def test_clear_cache(self, bounded_tif):
        source = RasterSource(bounded_tif)
        source.tile(0, 0, 0)
        assert source.cached_tiles == 1
        source.clear_cache()
        assert source.cached_tiles == 0


class TestViewerRaster:
    def test_add_raster_emits_provider(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        raster = viewer.add_raster(bounded_tif, name="bounded")
        html = viewer.to_html()
        assert raster.id in html
        assert f"/raster/{raster.id}/{{z}}/{{x}}/{{y}}.png" in html
        assert "UrlTemplateImageryProvider" in html

    def test_first_raster_is_base_layer(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        viewer.add_raster(bounded_tif)
        html = viewer.to_html()
        # baseLayer appears in the constructor options, not as a statement
        assert "baseLayer: new Cesium.ImageryLayer" in html
        assert "_rasterLayer" not in html

    def test_second_raster_stacks_as_overlay(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        viewer.add_raster(bounded_tif)
        second = viewer.add_raster(bounded_tif, name="second")
        html = viewer.to_html()
        assert "const _rasterLayer1 = viewer.imageryLayers.addImageryProvider(" in html
        assert f"/raster/{second.id}/{{z}}/{{x}}/{{y}}.png" in html

    def test_raster_opacity(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        viewer.add_raster(bounded_tif, opacity=0.4)
        viewer.add_raster(bounded_tif, name="second", opacity=0.6)
        html = viewer.to_html()
        assert "viewer.imageryLayers.get(0).alpha = 0.4;" in html
        assert "_rasterLayer1.alpha = 0.6;" in html

    def test_raster_opacity_validation(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        with pytest.raises(ValueError):
            viewer.add_raster(bounded_tif, opacity=1.5)
        for opacity in (True, float("nan"), float("inf")):
            with pytest.raises((TypeError, ValueError)):
                viewer.add_raster(bounded_tif, opacity=opacity)

    def test_add_wmts_layer(self):
        viewer = cesiumkit.Viewer()
        viewer.add_wmts_layer(
            "https://example.com/wmts",
            layer="topo",
            style="default",
            tile_matrix_set="EPSG:3857",
            format="image/png",
            maximum_level=18,
            opacity=0.7,
        )
        html = viewer.to_html()
        assert "const _wmtsLayer0 = viewer.imageryLayers.addImageryProvider(" in html
        assert "new Cesium.WebMapTileServiceImageryProvider({" in html
        assert 'layer: "topo"' in html
        assert 'style: "default"' in html
        assert 'tileMatrixSetID: "EPSG:3857"' in html
        assert 'format: "image/png"' in html
        assert "maximumLevel: 18" in html
        assert "_wmtsLayer0.alpha = 0.7;" in html

    def test_add_wmts_layer_defaults_implicit(self):
        viewer = cesiumkit.Viewer()
        viewer.add_wmts_layer("https://example.com/wmts", layer="topo")
        html = viewer.to_html()
        assert "_wmtsLayer0.alpha" not in html
        assert "maximumLevel:" not in html.replace("maximumLevel: 2", "")

    def test_add_wmts_opacity_validation(self):
        viewer = cesiumkit.Viewer()
        with pytest.raises(ValueError):
            viewer.add_wmts_layer("https://example.com/wmts", layer="topo", opacity=2)

    def test_add_wmts_layer_escapes_script_tags(self):
        viewer = cesiumkit.Viewer()
        viewer.add_wmts_layer(
            "https://example.com/wmts",
            layer="</script><script>alert(1)</script>",
        )
        html = viewer.to_html()
        assert "\\u003c/script\\u003e" in html
        assert 'layer: "</script>' not in html

    def test_maximum_level_must_be_int(self):
        viewer = cesiumkit.Viewer()
        with pytest.raises(TypeError):
            viewer.add_wmts_layer("https://example.com/wmts", layer="topo", maximum_level="1});fetch('https://evil')//")
        with pytest.raises(TypeError):
            viewer.add_raster("dummy.tif", maximum_level="18")
        with pytest.raises(TypeError):
            # bool is an int subclass but is not a valid zoom level
            viewer.add_wmts_layer("https://example.com/wmts", layer="topo", maximum_level=True)
        with pytest.raises(ValueError):
            viewer.add_wmts_layer("https://example.com/wmts", layer="topo", maximum_level=-1)

    def test_cross_kind_layers_keep_add_order(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        viewer.add_raster(bounded_tif)  # base layer
        viewer.add_wmts_layer("https://example.com/wmts", layer="topo")
        viewer.add_raster(bounded_tif, name="second")
        html = viewer.to_html()
        wmts_at = html.find("const _wmtsLayer1 = viewer.imageryLayers.addImageryProvider(")
        raster_at = html.find("const _rasterLayer2 = viewer.imageryLayers.addImageryProvider(")
        assert wmts_at != -1 and raster_at != -1
        assert wmts_at < raster_at, "layers must stack in add order, WMTS and raster alike"

    def test_wmts_first_then_raster(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        viewer.add_wmts_layer("https://example.com/wmts", layer="topo")
        viewer.add_raster(bounded_tif)
        html = viewer.to_html()
        # the raster still becomes the base layer; the WMTS is the overlay
        assert "const _wmtsLayer0 = viewer.imageryLayers.addImageryProvider(" in html
        assert "const _rasterLayer" not in html

    def test_add_raster_warns_when_replacing_imagery_provider(self, bounded_tif):
        viewer = cesiumkit.Viewer(
            imagery_provider=cesiumkit.UrlTemplateImageryProvider(url="https://example.com/{z}/{x}/{y}.png")
        )
        with pytest.warns(UserWarning):
            viewer.add_raster(bounded_tif)

    def test_add_raster_fails_fast_for_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            cesiumkit.Viewer().add_raster(tmp_path / "missing.tif")

    def test_add_points_colormap_convenience(self, bounded_tif):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        import shapely.geometry

        gdf = gpd.GeoDataFrame(
            {"value": [1, 2, 3]},
            geometry=[shapely.geometry.Point(x, y) for x, y in [(0, 0), (1, 1), (2, 2)]],
            crs="EPSG:4326",
        )
        viewer = cesiumkit.Viewer()
        viewer.add_points(gdf, colormap=["#000000", "#ff0000"], plot_width=256, plot_height=256)
        html = viewer.to_html()
        assert "UrlTemplateImageryProvider" in html

    def test_stacked_rasters_render(self, bounded_tif):
        """The generated layer statements must run, not just exist."""
        from cesiumkit import _vendor

        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        pytest.importorskip("playwright")
        from cesiumkit.testing import render_state

        viewer = cesiumkit.Viewer()
        viewer.add_raster(bounded_tif, opacity=0.6)
        viewer.add_raster(bounded_tif, name="second", opacity=0.8)
        viewer.add_wmts_layer("https://example.com/wmts", layer="topo", opacity=0.5)
        state = render_state(viewer, wait_ms=6000)
        assert not state["pageErrors"], state["pageErrors"]

    def test_raster_tile_route_serves_png(self, bounded_tif):
        viewer = cesiumkit.Viewer()
        raster = viewer.add_raster(bounded_tif)
        with OfflineServer(viewer) as server:
            status, body = server.get(f"/raster/{raster.id}/0/0/0.png")
            assert status == 200
            assert body[:8] == b"\x89PNG\r\n\x1a\n"

    def test_unknown_raster_source_404(self):
        viewer = cesiumkit.Viewer()
        with OfflineServer(viewer) as server:
            import urllib.error

            with pytest.raises(urllib.error.HTTPError) as excinfo:
                server.get("/raster/nope/0/0/0.png")
            assert excinfo.value.code == 404

    def test_bad_tile_coordinates_400(self):
        viewer = cesiumkit.Viewer()
        with OfflineServer(viewer) as server:
            import urllib.error

            with pytest.raises(urllib.error.HTTPError) as excinfo:
                server.get("/raster/abc/notanumber/0/0.png")
            assert excinfo.value.code == 400


class TestAggregatePoints:
    def test_aggregate_and_serve(self):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame(
            geometry=[Point(-75, 40), Point(-74, 41), Point(-73, 39)],
            crs="EPSG:4326",
        )
        path = Path(cesiumkit.aggregate_points_to_raster(gdf))
        try:
            with RasterSource(path) as source:
                body = source.tile(0, 0, 0)
                assert body is not None
                assert body[:8] == b"\x89PNG\r\n\x1a\n"
                assert io.BytesIO(body).getbuffer().nbytes > 0
        finally:
            path.unlink(missing_ok=True)

    def test_add_points_wires_raster_layer(self):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame(geometry=[Point(-75, 40), Point(-74, 41)], crs="EPSG:4326")
        viewer = cesiumkit.Viewer()
        raster = viewer.add_points(gdf)
        assert isinstance(raster, RasterSource)
        html = viewer.to_html()
        assert f"/raster/{raster.id}/" in html
        assert "UrlTemplateImageryProvider" in html
        viewer.close()

    def test_add_points_forwards_layer_options_and_rejects_unknown_options(self):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame(geometry=[Point(-75, 40), Point(-74, 41)], crs="EPSG:4326")
        viewer = cesiumkit.Viewer()
        viewer.add_points(gdf, opacity=0.5, maximum_level=8)
        assert "viewer.imageryLayers.get(0).alpha = 0.5" in viewer.to_html()
        viewer.close()
        with pytest.raises(TypeError, match="unexpected aggregation options"):
            cesiumkit.Viewer().add_points(gdf, unsupported=True)

    def test_aggregate_rejects_missing_crs_and_non_points(self):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        from shapely.geometry import LineString, Point

        with pytest.raises(ValueError, match="coordinate reference system"):
            cesiumkit.aggregate_points_to_raster(gpd.GeoDataFrame(geometry=[Point(0, 0)]))
        with pytest.raises(ValueError, match="Point geometries"):
            cesiumkit.aggregate_points_to_raster(
                gpd.GeoDataFrame(geometry=[LineString([(0, 0), (1, 1)])], crs="EPSG:4326")
            )

    def test_viewer_close_removes_owned_aggregate_raster(self):
        pytest.importorskip("datashader")
        pytest.importorskip("geopandas")
        import geopandas as gpd
        from shapely.geometry import Point

        viewer = cesiumkit.Viewer()
        raster = viewer.add_points(gpd.GeoDataFrame(geometry=[Point(-75, 40), Point(-74, 41)], crs="EPSG:4326"))
        path = Path(raster.path)
        assert path.is_file()
        viewer.close()
        assert not path.exists()
