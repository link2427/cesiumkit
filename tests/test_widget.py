"""Tests for the Jupyter widget (requires the [widget] extras)."""

import json
import shutil
import subprocess

import pytest

pytest.importorskip("anywidget")

import cesiumkit  # noqa: E402
from cesiumkit import _vendor  # noqa: E402
from cesiumkit.widget import CesiumKitWidget  # noqa: E402


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
            widget._handle_msg(
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
        widget._handle_msg(widget, {"type": "event", "event": "click", "result": "abc"}, [])
        assert clicked == ["abc"]


class TestWidgetRender:
    """Render the widget ESM headlessly with a mock anywidget model."""

    def test_esm_renders_viewer(self, playwright_browser):
        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        import functools
        import http.server
        import socketserver
        import tempfile
        import threading
        from pathlib import Path

        widget = CesiumKitWidget(_viewer(), height="400px")
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
                errors = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/harness.html")
                page.wait_for_timeout(8000)
                ok = page.evaluate("() => !!(window.viewer && window.viewer.scene && window.viewer.scene.globe)")
                imagery = page.evaluate("() => window.viewer ? window.viewer.imageryLayers.length : 0")
                page.close()
                httpd.shutdown()
        assert ok, f"viewer did not initialize: {errors}"
        assert imagery >= 1
