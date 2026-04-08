"""Tests for cesiumkit.viewer module."""

import cesiumkit


class TestViewer:
    def test_basic_creation(self):
        v = cesiumkit.Viewer()
        html = v.to_html()
        assert "Cesium.Viewer" in html
        assert "cesiumContainer" in html

    def test_with_ion_token(self):
        v = cesiumkit.Viewer(ion_token="my_token_123")
        html = v.to_html()
        assert "my_token_123" in html
        assert "Ion.defaultAccessToken" in html

    def test_widget_options(self):
        v = cesiumkit.Viewer(animation=False, timeline=False, geocoder=False)
        html = v.to_html()
        assert "animation: false" in html
        assert "timeline: false" in html
        assert "geocoder: false" in html

    def test_add_entity(self):
        v = cesiumkit.Viewer()
        v.add_entity(cesiumkit.Entity(
            name="Test Point",
            position=cesiumkit.Cartesian3.from_degrees(-75, 40),
            point=cesiumkit.PointGraphics(pixel_size=10, color=cesiumkit.Color.RED),
        ))
        html = v.to_html()
        assert "viewer.entities.add" in html
        assert "Test Point" in html
        assert "pixelSize" in html

    def test_multiple_entities(self):
        v = cesiumkit.Viewer()
        v.add_entity(cesiumkit.Entity(name="A", point=cesiumkit.PointGraphics(pixel_size=5)))
        v.add_entity(cesiumkit.Entity(name="B", point=cesiumkit.PointGraphics(pixel_size=10)))
        html = v.to_html()
        assert html.count("viewer.entities.add") == 2

    def test_cesium_version(self):
        v = cesiumkit.Viewer(cesium_version="1.115")
        html = v.to_html()
        assert "releases/1.115/" in html

    def test_custom_container(self):
        v = cesiumkit.Viewer(container_id="myContainer")
        html = v.to_html()
        assert "myContainer" in html

    def test_save(self, tmp_path):
        v = cesiumkit.Viewer()
        path = tmp_path / "test.html"
        v.save(str(path))
        content = path.read_text()
        assert "Cesium.Viewer" in content

    def test_repr_html(self):
        v = cesiumkit.Viewer()
        html = v._repr_html_()
        assert "<iframe" in html

    def test_fly_to(self):
        v = cesiumkit.Viewer()
        v.fly_to(cesiumkit.Cartesian3.from_degrees(-75, 40, 15000), duration=3.0)
        html = v.to_html()
        assert "camera.flyTo" in html
        assert "fromDegrees" in html

    def test_set_view(self):
        v = cesiumkit.Viewer()
        v.set_view(cesiumkit.Cartesian3.from_degrees(-75, 40, 15000))
        html = v.to_html()
        assert "camera.setView" in html

    def test_add_script(self):
        v = cesiumkit.Viewer()
        v.add_script("console.log('hello');")
        html = v.to_html()
        assert "console.log('hello')" in html

    def test_load_geojson(self):
        v = cesiumkit.Viewer()
        v.load_geojson(url="https://example.com/data.geojson")
        html = v.to_html()
        assert "GeoJsonDataSource" in html
        assert "dataSources.add" in html

    def test_load_czml(self):
        v = cesiumkit.Viewer()
        v.load_czml(url="https://example.com/data.czml")
        html = v.to_html()
        assert "CzmlDataSource" in html

    def test_add_tileset(self):
        v = cesiumkit.Viewer()
        v.add_tileset(ion_asset_id=75343)
        html = v.to_html()
        assert "Cesium3DTileset" in html
        assert "75343" in html

    def test_event_handler(self):
        v = cesiumkit.Viewer()
        v.on(
            cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
            "function(click) { console.log(click); }",
        )
        html = v.to_html()
        assert "ScreenSpaceEventHandler" in html
        assert "LEFT_CLICK" in html


class TestViewerCzmlExport:
    def test_basic_czml_export(self):
        v = cesiumkit.Viewer()
        v.add_entity(cesiumkit.Entity(
            id="test-1",
            name="Test",
            position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
        ))
        czml = v.to_czml()
        assert len(czml) == 2  # preamble + 1 entity
        assert czml[0]["id"] == "document"
        assert czml[1]["id"] == "test-1"

    def test_czml_string(self):
        v = cesiumkit.Viewer()
        v.add_entity(cesiumkit.Entity(id="e1", name="E1"))
        s = v.to_czml_string()
        assert '"document"' in s
        assert '"e1"' in s

    def test_save_czml(self, tmp_path):
        v = cesiumkit.Viewer()
        v.add_entity(cesiumkit.Entity(id="e1", name="E1"))
        path = tmp_path / "test.czml"
        v.save_czml(str(path))
        content = path.read_text()
        assert '"document"' in content
