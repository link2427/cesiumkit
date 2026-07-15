"""Tests for cesiumkit.viewer module."""

from collections import deque

import pytest

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
        v.add_entity(
            cesiumkit.Entity(
                name="Test Point",
                position=cesiumkit.Cartesian3.from_degrees(-75, 40),
                point=cesiumkit.PointGraphics(pixel_size=10, color=cesiumkit.Color.RED),
            )
        )
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

    def test_runtime_clock_commands_escape_input(self):
        v = cesiumkit.Viewer()
        v.set_time("2024-01-01T00:00:00Z'); alert('nope")
        commands = list(v._command_queue)
        assert len(commands) == 2
        assert "fromIso8601(\"2024-01-01T00:00:00Z'); alert('nope\")" in commands[0]["js"]
        assert "if (viewer.timeline)" in commands[1]["js"]

    def test_runtime_clock_controls(self):
        v = cesiumkit.Viewer()
        v.animate(False)
        v.set_multiplier(60)
        commands = [command["js"] for command in v._command_queue]
        assert "viewer.clock.shouldAnimate = false;" in commands
        assert "viewer.clock.multiplier = 60;" in commands

    def test_multiplier_must_be_finite(self):
        with pytest.raises(ValueError, match="finite"):
            cesiumkit.Viewer().set_multiplier(float("nan"))

    def test_runtime_bridge_is_rendered(self):
        html = cesiumkit.Viewer().to_html()
        assert "/__cesiumkit_cmd" in html
        assert "/__cesiumkit_result" in html
        assert "__cesiumkitPostResult" in html

    def test_wait_for_runtime_result(self):
        v = cesiumkit.Viewer()
        v._runtime_results["request-1"] = "2024-01-01T00:00:00Z"
        assert v._wait_for_runtime_result("request-1", timeout=0) == "2024-01-01T00:00:00Z"

    def test_get_current_time_requires_running_server(self):
        with pytest.raises(RuntimeError, match="show"):
            cesiumkit.Viewer().get_current_time(timeout=0)

    def test_runtime_queue_uses_deque(self):
        assert isinstance(cesiumkit.Viewer()._command_queue, deque)

    def test_update_czml_accepts_packets_and_targets_matching_source(self):
        v = cesiumkit.Viewer()
        packets = [{"id": "document", "version": "1.0"}, {"id": "sat-1"}]
        v.update_czml(packets)
        command = v._command_queue[-1]["js"]
        assert '"sat-1"' in command
        assert "candidate instanceof Cesium.CzmlDataSource" in command
        assert "collection.get(0)" not in command

    def test_update_geojson_escapes_urls(self):
        v = cesiumkit.Viewer()
        v.update_geojson("https://example.com/o'hare.geojson")
        command = v._command_queue[-1]["js"]
        assert '"https://example.com/o\'hare.geojson"' in command
        assert "Cesium.GeoJsonDataSource.load" in command

    def test_poll_czml_can_be_stopped(self):
        v = cesiumkit.Viewer()
        poller_id = v.poll_czml("https://example.com/live.czml", interval=2.5)
        assert poller_id
        assert "setInterval" in v._command_queue[-1]["js"]
        assert "2500.0" in v._command_queue[-1]["js"]
        v.stop_polling(poller_id)
        assert poller_id in v._command_queue[-1]["js"]
        assert "clearInterval" in v._command_queue[-1]["js"]

    def test_runtime_update_interval_validation(self):
        v = cesiumkit.Viewer()
        with pytest.raises(ValueError, match="positive"):
            v.poll_czml("https://example.com/live.czml", interval=0)
        with pytest.raises(ValueError, match="positive"):
            v.stream_czml([], interval=float("inf"))

    def test_stream_czml_queues_each_batch(self):
        v = cesiumkit.Viewer()
        thread = v.stream_czml([[{"id": "one"}], [{"id": "two"}]], interval=0.001)
        thread.join(timeout=1)
        assert not thread.is_alive()
        commands = [command["js"] for command in v._command_queue]
        assert any('"one"' in command for command in commands)
        assert any('"two"' in command for command in commands)

    def test_select_entity_escapes_id(self):
        v = cesiumkit.Viewer()
        v.select_entity("sat'1")
        command = v._command_queue[-1]["js"]
        assert 'getById("sat\'1")' in command
        assert "requestRender" in command

    def test_pick_returns_local_entity(self, monkeypatch):
        v = cesiumkit.Viewer()
        entity = v.add_entity(cesiumkit.Entity(id="sat-1"))
        monkeypatch.setattr(v, "_request_runtime_result", lambda expression, *, timeout: "sat-1")
        assert v.pick(cesiumkit.Cartesian2(x=10, y=20)) is entity

    def test_pick_validates_screen_position(self):
        v = cesiumkit.Viewer()
        with pytest.raises(ValueError, match="finite"):
            v.pick(cesiumkit.Cartesian2(x=float("inf"), y=20))

    def test_selected_entity_returns_local_entity(self, monkeypatch):
        v = cesiumkit.Viewer()
        entity = v.add_entity(cesiumkit.Entity(id="selected"))
        monkeypatch.setattr(v, "_get_selected_entity_id", lambda: "selected")
        assert v.selected_entity is entity

    def test_drill_pick_filters_nonlocal_entities(self, monkeypatch):
        v = cesiumkit.Viewer()
        local = v.add_entity(cesiumkit.Entity(id="local"))
        monkeypatch.setattr(
            v,
            "_request_runtime_result",
            lambda expression, *, timeout: ["local", "external"],
        )
        assert v.drill_pick(cesiumkit.Cartesian2(x=1, y=2)) == [local]

    def test_screenshot_base64_uses_runtime_result(self, monkeypatch):
        v = cesiumkit.Viewer()
        monkeypatch.setattr(v, "_request_runtime_result", lambda expression, *, timeout: "cG5n")
        assert v.screenshot_base64(timeout=1) == "cG5n"

    def test_screenshot_writes_decoded_png(self, tmp_path, monkeypatch):
        v = cesiumkit.Viewer()
        monkeypatch.setattr(v, "screenshot_base64", lambda *, timeout: "cG5n")
        path = tmp_path / "viewer.png"
        v.screenshot(path)
        assert path.read_bytes() == b"png"

    def test_screenshot_rejects_malformed_base64(self, monkeypatch):
        v = cesiumkit.Viewer()
        monkeypatch.setattr(v, "screenshot_base64", lambda *, timeout: "not base64!")
        with pytest.raises(RuntimeError, match="malformed"):
            v.screenshot("unused.png")

    def test_canvas_to_image(self, monkeypatch):
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        v = cesiumkit.Viewer()
        monkeypatch.setattr(v, "screenshot_base64", lambda *, timeout: png)
        image = v.canvas_to_image()
        assert image.size == (1, 1)


class TestViewerCzmlExport:
    def test_basic_czml_export(self):
        v = cesiumkit.Viewer()
        v.add_entity(
            cesiumkit.Entity(
                id="test-1",
                name="Test",
                position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
            )
        )
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
