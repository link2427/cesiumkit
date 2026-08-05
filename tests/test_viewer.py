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

    def test_performance_controls(self):
        v = cesiumkit.Viewer(
            request_render_mode=True,
            maximum_render_time_change=0.5,
            resolution_scale=0.75,
            target_frame_rate=30,
            show_renderer_errors=False,
        )
        html = v.to_html()
        assert "requestRenderMode: true" in html
        assert "maximumRenderTimeChange: 0.5" in html
        assert "viewer.resolutionScale = 0.75" in html
        assert "targetFrameRate: 30" in html
        assert "showRenderLoopErrors: false" in html

    @pytest.mark.parametrize(
        ("keyword", "value"),
        [
            ("maximum_render_time_change", -1),
            ("resolution_scale", 0),
            ("resolution_scale", float("inf")),
            ("target_frame_rate", 0),
        ],
    )
    def test_performance_control_validation(self, keyword, value):
        with pytest.raises(ValueError):
            cesiumkit.Viewer(**{keyword: value})

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

    def test_cesium_version_rejected(self):
        # the escape hatch was removed in 1.0; the bundled build is pinned
        with pytest.raises(TypeError):
            cesiumkit.Viewer(cesium_version="1.115")

    def test_default_cesium_version(self):
        html = cesiumkit.Viewer().to_html()
        assert "releases/1.144/" in html

    def test_imagery_provider_uses_base_layer(self):
        v = cesiumkit.Viewer(
            ion_token="tok",
            imagery_provider=cesiumkit.IonImageryProvider(asset_id=75343),
        )
        html = v.to_html()
        assert "baseLayer: new Cesium.ImageryLayer(new Cesium.IonImageryProvider({" in html
        assert "imageryProvider:" not in html

    def test_terrain_provider_assigned_after_viewer_creation(self):
        v = cesiumkit.Viewer(
            terrain_provider=cesiumkit.CesiumTerrainProvider(url="https://assets.cesium.com/1"),
        )
        html = v.to_html()
        assert "viewer.scene.terrainProvider = await Cesium.CesiumTerrainProvider.fromUrl(" in html
        assert "terrainProvider:" not in html

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

    def test_tileset_options_serialize_when_explicit(self):
        v = cesiumkit.Viewer()
        v.add_tileset(ion_asset_id=75343, maximum_memory_usage=536870912, maximum_screen_space_error=4.0)
        html = v.to_html()
        assert "maximumMemoryUsage: 536870912" in html
        assert "maximumScreenSpaceError: 4.0" in html

    def test_tileset_defaults_stay_implicit(self):
        v = cesiumkit.Viewer()
        v.add_tileset(ion_asset_id=75343)
        html = v.to_html()
        assert "Cesium.Cesium3DTileset.fromIonAssetId(75343)" in html
        assert "maximumScreenSpaceError" not in html

    def test_tileset_style_emits_cesium_3d_tile_style(self):
        v = cesiumkit.Viewer()
        v.add_tileset(
            ion_asset_id=75343,
            style=cesiumkit.Cesium3DTileStyle(
                color_conditions=[("${Height} < 100", "color('red')"), ("true", "color('blue')")],
                point_size=4.0,
            ),
        )
        html = v.to_html()
        assert "tileset.style = new Cesium.Cesium3DTileStyle({" in html
        assert "\"${Height} < 100\", color('red')" in html
        assert "pointSize: 4.0" in html

    def test_fly_to_entities(self):
        v = cesiumkit.Viewer()
        v.fly_to_entities(duration=2.0)
        html = v.to_html()
        assert "viewer.flyTo(viewer.entities, {" in html
        assert "duration: 2.0" in html

    def test_fly_to_bounding_sphere(self):
        v = cesiumkit.Viewer()
        v.fly_to_bounding_sphere(cesiumkit.Cartesian3.from_degrees(-75, 40, 1000), duration=1.5)
        html = v.to_html()
        assert "viewer.camera.flyToBoundingSphere(" in html
        assert "duration: 1.5" in html

    def test_add_particle_system_primitive(self):
        v = cesiumkit.Viewer()
        particle = v.add_particle_system(
            image="smoke.png",
            emission_rate=10,
            particle_life=2,
            start_scale=1,
            end_scale=0.1,
        )
        assert isinstance(particle, cesiumkit.ParticleSystem)
        html = v.to_html()
        assert "viewer.scene.primitives.add" in html
        assert "new Cesium.ParticleSystem" in html
        assert 'image: "smoke.png"' in html

    def test_particle_system_validates_ranges(self):
        with pytest.raises(ValueError, match="maximum_speed"):
            cesiumkit.ParticleSystem(image="smoke.png", minimum_speed=10, maximum_speed=5)

    def test_event_handler(self):
        v = cesiumkit.Viewer()
        v.on(
            cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
            "function(click) { console.log(click); }",
        )
        html = v.to_html()
        assert "ScreenSpaceEventHandler" in html
        assert "LEFT_CLICK" in html

    def test_python_click_bridge_uses_public_entity_id_and_click_position(self):
        v = cesiumkit.Viewer()
        v.on_click(lambda entity_id: None)
        html = v.to_html()
        assert "movement.position" in html
        assert "picked.id.id" in html
        assert "endPosition" not in html
        assert "picked.id._id" not in html
        assert "__cesiumkitPostEvent('click', entityId)" in html

    def test_python_click_bridge_is_registered_once(self):
        v = cesiumkit.Viewer()
        v.on_click(lambda entity_id: None)
        v.on_click(lambda entity_id: None)
        assert v.to_html().count("window.__cesiumkitClickHandler = handler") == 1

    def test_python_click_callbacks_and_waiter_receive_event(self):
        received = []
        v = cesiumkit.Viewer()
        v.on_click(received.append)
        v._handle_runtime_event("click", "sat-1")
        assert received == ["sat-1"]
        assert v.wait_for_click(timeout=0) == "sat-1"

    def test_wait_for_click_times_out(self):
        v = cesiumkit.Viewer()
        with pytest.raises(TimeoutError, match="No click"):
            v.wait_for_click(timeout=0)
        assert "ScreenSpaceEventHandler" in v.to_html()

    def test_click_callback_exceptions_are_logged(self, caplog):
        v = cesiumkit.Viewer()

        def broken_callback(entity_id):
            raise RuntimeError("boom")

        v.on_click(broken_callback)
        v._handle_runtime_event("click", None)
        assert "Unhandled exception" in caplog.text

    def test_on_click_after_show_queues_runtime_registration(self):
        v = cesiumkit.Viewer()
        v._server = object()
        v.on_click(lambda entity_id: None)
        assert "ScreenSpaceEventHandler" in v._command_queue[-1]["js"]

    def test_on_click_requires_callable(self):
        with pytest.raises(TypeError, match="callable"):
            cesiumkit.Viewer().on_click(None)

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
