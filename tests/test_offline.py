"""Tests for offline serving of the bundled Cesium build.

These require the vendored build (cesiumkit/vendor/), produced by
scripts/fetch_cesium.py. CI runs them in the dedicated `offline` job.
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request

import pytest

import cesiumkit
from cesiumkit import _vendor

pytestmark = pytest.mark.skipif(
    _vendor.vendor_dir() is None,
    reason="bundled Cesium build not present; run scripts/fetch_cesium.py",
)


class OfflineServer:
    def __init__(self, viewer: cesiumkit.Viewer):
        self.viewer = viewer

    def __enter__(self) -> OfflineServer:
        thread = threading.Thread(
            target=self.viewer.show,
            kwargs={"port": 0, "open_browser": False},
            daemon=True,
        )
        thread.start()
        for _ in range(200):
            if self.viewer._server is not None:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("server did not start")
        self.port = self.viewer._server.server_address[1]
        return self

    def __exit__(self, *exc) -> None:
        self.viewer.close()

    def get(self, path: str) -> tuple[int, bytes]:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=10) as response:
            return response.status, response.read()


def _simple_viewer() -> cesiumkit.Viewer:
    viewer = cesiumkit.Viewer(title="offline")
    viewer.add_entity(
        cesiumkit.Entity(
            name="NYC",
            position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
            point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
        )
    )
    return viewer


class TestVendorBuild:
    def test_version_marker_matches_default(self):
        vendor = _vendor.vendor_dir()
        assert vendor is not None
        assert (vendor / ".cesiumkit-version").read_text().strip() == "1.144"


class TestOfflineServing:
    def test_served_html_uses_local_vendor(self):
        with OfflineServer(_simple_viewer()) as server:
            status, body = server.get("/index.html")
            assert status == 200
            html = body.decode("utf-8")
            assert "/vendor/cesium/Cesium.js" in html
            assert "/vendor/cesium/Widgets/widgets.css" in html
            assert "cesium.com" not in html

    def test_vendor_cesium_js_served(self):
        with OfflineServer(_simple_viewer()) as server:
            status, body = server.get("/vendor/cesium/Cesium.js")
            assert status == 200
            assert len(body) > 500_000

    def test_vendor_widgets_css_served(self):
        with OfflineServer(_simple_viewer()) as server:
            status, body = server.get("/vendor/cesium/Widgets/widgets.css")
            assert status == 200
            assert len(body) > 1_000

    def test_bundled_natural_earth_tile_served(self):
        with OfflineServer(_simple_viewer()) as server:
            status, _ = server.get("/vendor/cesium/Assets/Textures/NaturalEarthII/0/0/0.jpg")
            assert status == 200

    def test_path_traversal_does_not_escape_vendor_dir(self):
        with OfflineServer(_simple_viewer()) as server:
            for path in (
                "/vendor/cesium/../../pyproject.toml",
                "/vendor/cesium/../../../../etc/passwd",
                "/vendor/cesium/%2e%2e/%2e%2e/etc/passwd",
            ):
                with pytest.raises(urllib.error.HTTPError) as excinfo:
                    server.get(path)
                assert excinfo.value.code == 404, path
