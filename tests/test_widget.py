"""Tests for the Jupyter widget (requires the [widget] extras)."""

import json
import re
import shutil
import subprocess
from contextlib import contextmanager

import pytest

pytest.importorskip("anywidget")

import cesiumkit  # noqa: E402
from cesiumkit import _vendor  # noqa: E402
from cesiumkit.widget import CesiumKitWidget  # noqa: E402


@contextmanager
def _serve_esm(widget, playwright_browser):
    """Serve the widget ESM in a mock-anywidget harness; yields the loaded page."""
    import functools
    import http.server
    import socketserver
    import tempfile
    import threading
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "widget.mjs").write_text(widget._esm, encoding="utf-8")
        (root / "harness.html").write_text(
            """<!DOCTYPE html>
<html><body>
<div id="target"></div>
<script>
window.__model = {
    get: (key) => key === 'state' ? window.__state : undefined,
    on: () => {},
    send: () => {},
};
</script>
<script type="module">
import widget from './widget.mjs';
window.__state = JSON.parse(document.getElementById('state').textContent);
widget.render({ model: window.__model, el: document.getElementById('target') });
</script>
<pre id="state" style="display:none">STATE_JSON</pre>
</body></html>""".replace("STATE_JSON", json.dumps(widget.state)),
            encoding="utf-8",
        )
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
        with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            page = playwright_browser.new_page()
            page.on("pageerror", lambda exc: print(f"    [pageerror] {exc}"))
            page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/harness.html")
            page.wait_for_timeout(8000)
            try:
                yield page
            finally:
                page.close()
                httpd.shutdown()


def _viewer():
    viewer = cesiumkit.Viewer(title="widget test")
    viewer.add_entity(
        cesiumkit.Entity(
            name="NYC",
            position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
            point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
        )
    )
    return viewer


def _viewer_with_custom_data_source():
    viewer = cesiumkit.Viewer(title="widget ds test")
    ds = cesiumkit.CustomDataSource(name="my_sources")
    ds.entities.add(
        cesiumkit.Entity(
            name="Custom",
            position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
            point=cesiumkit.PointGraphics(pixel_size=5),
        )
    )
    viewer.add_data_source(ds)
    return viewer


class TestWidgetState:
    def test_constructs_and_serializes_viewer(self):
        widget = CesiumKitWidget(_viewer())
        state = widget.state
        assert state["ionToken"] == ""
        assert "NYC" in json.dumps(state["entities"])
        assert "https://cesium.com" in state["cesiumUrl"]

    def test_to_widget_convenience(self):
        widget = _viewer().to_widget()
        assert isinstance(widget, CesiumKitWidget)

    def test_lazy_top_level_export(self):
        assert cesiumkit.CesiumKitWidget is CesiumKitWidget

    def test_state_keys_match_esm_reads(self):
        """Every `state.X` the ESM reads must exist in the widget state."""
        widget = CesiumKitWidget(_viewer_with_custom_data_source())
        esm_keys = set(re.findall(r"state\.([A-Za-z][A-Za-z0-9]*)", widget._esm))
        # Keys set directly in __init__ (not via _doc_parts).
        init_keys = {"height", "cesiumUrl", "ionToken"}
        missing = esm_keys - init_keys - set(widget.state)
        assert not missing, f"ESM reads state keys missing from widget.state: {sorted(missing)}"

    def test_custom_data_source_entities_serialized(self):
        widget = CesiumKitWidget(_viewer_with_custom_data_source())
        assert 'new Cesium.CustomDataSource("my_sources")' in widget.state["dataSources"][0]
        assert "_ds.entities.add(" in widget.state["dataSourceEntityStatements"][0][0]


class TestEsmSyntax:
    def test_esm_is_valid_javascript(self):
        node = shutil.which("node")
        if node is None:
            pytest.skip("node not available")
        with open("/tmp/cesiumkit_widget.mjs", "w", encoding="utf-8") as f:
            f.write(CesiumKitWidget._esm)
        result = subprocess.run(
            [node, "--check", "/tmp/cesiumkit_widget.mjs"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


class TestBridgePythonSide:
    def test_command_roundtrip(self):
        widget = CesiumKitWidget(_viewer())
        sent = {}

        def fake_send(content):
            sent["content"] = content
            # Simulate the JS side replying synchronously.
            widget._on_widget_message(
                widget,
                {"type": "result", "requestId": content["requestId"], "result": "2026-01-01T00:00:00Z"},
                [],
            )

        widget.send = fake_send  # type: ignore[method-assign]
        assert widget.get_current_time(timeout=5.0) == "2026-01-01T00:00:00Z"
        assert sent["content"]["type"] == "command"

    def test_click_event_fires_callback(self):
        widget = CesiumKitWidget(_viewer())
        clicked = []
        widget.on_click(lambda entity_id: clicked.append(entity_id))
        widget._on_widget_message(widget, {"type": "event", "event": "click", "result": "abc"}, [])
        assert clicked == ["abc"]


class TestWidgetRender:
    """Render the widget ESM headlessly with a mock anywidget model."""

    def test_esm_renders_viewer(self, playwright_browser):
        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        with _serve_esm(CesiumKitWidget(_viewer(), height="400px"), playwright_browser) as page:
            ok = page.evaluate("() => !!(window.viewer && window.viewer.scene && window.viewer.scene.globe)")
            imagery = page.evaluate("() => window.viewer ? window.viewer.imageryLayers.length : 0")
        assert ok, "viewer did not initialize"
        assert imagery >= 1

    def test_esm_renders_custom_data_source_entities(self, playwright_browser):
        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        widget = CesiumKitWidget(_viewer_with_custom_data_source(), height="400px")
        with _serve_esm(widget, playwright_browser) as page:
            state = page.evaluate(
                """() => {
                    const ds = window.viewer.dataSources.get(0);
                    return {
                        name: ds ? ds.name : null,
                        entityCount: ds ? ds.entities.values.length : -1,
                    };
                }"""
            )
        assert state == {"name": "my_sources", "entityCount": 1}, state
