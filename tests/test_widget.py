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
from cesiumkit._deprecations import CesiumkitDeprecationWarning  # noqa: E402
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

        class Handler(http.server.SimpleHTTPRequestHandler):
            # Windows does not consistently register .mjs in mimetypes; a
            # module script with the fallback MIME type is rejected by Chromium.
            extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript"}

        handler = functools.partial(Handler, directory=str(root))
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

    def test_cesium_version_is_release_pinned(self):
        widget = CesiumKitWidget(_viewer())
        assert "/releases/1.144/" in widget.state["cesiumUrl"]
        assert "/releases/1.144/" in widget.state["cesiumCssUrl"]
        assert widget.state["cesiumCssUrl"].endswith("/Widgets/widgets.css")

    def test_cesium_version_override_remains_deprecated_compatibility_path(self):
        with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
            widget = CesiumKitWidget(_viewer(), cesium_version="1.115")
        assert "/releases/1.115/" in widget.state["cesiumUrl"]
        assert "/releases/1.115/" in widget.state["cesiumCssUrl"]

    @pytest.mark.parametrize("version", ["", "latest", "1.144/evil", 1144])
    def test_cesium_version_override_is_strictly_validated(self, version):
        with pytest.raises((TypeError, ValueError)):
            CesiumKitWidget(_viewer(), cesium_version=version)

    def test_to_widget_convenience(self):
        widget = _viewer().to_widget()
        assert isinstance(widget, CesiumKitWidget)

    def test_to_widget_forwards_deprecated_version_override(self):
        with pytest.warns(CesiumkitDeprecationWarning):
            widget = _viewer().to_widget(cesium_version="1.115")
        assert "/releases/1.115/" in widget.state["cesiumUrl"]

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
    def test_esm_is_valid_javascript(self, tmp_path):
        node = shutil.which("node")
        if node is None:
            pytest.skip("node not available")
        esm_path = tmp_path / "cesiumkit_widget.mjs"
        esm_path.write_text(CesiumKitWidget._esm, encoding="utf-8")
        result = subprocess.run(
            [node, "--check", str(esm_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_esm_has_deterministic_cleanup(self):
        esm = CesiumKitWidget._esm
        assert "model.off('msg:custom', onCustomMessage)" in esm
        assert "handler.destroy()" in esm
        assert "viewer.destroy()" in esm

    def test_esm_loads_widget_css_and_disables_tokenless_services(self):
        esm = CesiumKitWidget._esm
        assert "_loadStylesheet(cssUrl)" in esm
        assert "_loadCesium(state.cesiumUrl, state.cesiumCssUrl)" in esm
        assert "link.dataset.cesiumkitCss" in esm
        assert "if (!state.ionToken)" in esm


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

    def test_command_timeout_clears_pending_request(self):
        widget = CesiumKitWidget(_viewer())
        widget.send = lambda content: None  # type: ignore[method-assign]

        with pytest.raises(TimeoutError, match="widget command timed out"):
            widget._send_command("1 + 1", timeout=0)

        assert widget._pending == {}

    def test_click_event_fires_callback(self):
        widget = CesiumKitWidget(_viewer())
        clicked = []
        widget.on_click(lambda entity_id: clicked.append(entity_id))
        widget._on_widget_message(widget, {"type": "event", "event": "click", "result": "abc"}, [])
        assert clicked == ["abc"]

    def test_runtime_arguments_are_validated(self):
        widget = CesiumKitWidget(_viewer())
        with pytest.raises(TypeError, match="bool"):
            widget.animate("false")
        with pytest.raises(TypeError, match="ISO-8601"):
            widget.set_time(123)
        with pytest.raises(TypeError, match="callable"):
            widget.on_click(None)
        with pytest.raises((TypeError, ValueError), match="timeout"):
            widget._send_command("1 + 1", timeout=float("nan"))

    @pytest.mark.parametrize("multiplier", [True, "1; alert(1)", float("nan"), float("inf")])
    def test_multiplier_rejects_non_finite_or_non_numeric_values(self, multiplier):
        widget = CesiumKitWidget(_viewer())
        with pytest.raises((TypeError, ValueError)):
            widget.set_multiplier(multiplier)


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
