"""Tests for cesiumkit.testing headless rendering helpers (playwright)."""

import os

import pytest

pytest.importorskip("playwright")

import cesiumkit  # noqa: E402
from cesiumkit import testing  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("CI") and not os.environ.get("CESIUMKIT_RENDER_TESTS"),
    reason="render tests are slow; enable with CESIUMKIT_RENDER_TESTS=1",
)


def _simple_viewer() -> cesiumkit.Viewer:
    viewer = cesiumkit.Viewer(title="render test")
    viewer.add_entity(
        cesiumkit.Entity(
            name="NYC",
            position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
            point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
        )
    )
    return viewer


class TestRenderState:
    def test_viewer_initializes(self):
        state = testing.render_state(_simple_viewer(), wait_ms=2000)
        assert state["ok"] is True
        assert state["pageErrors"] == []


class TestRenderScreenshot:
    def test_writes_png(self, tmp_path):
        out = str(tmp_path / "shot.png")
        testing.render_screenshot(_simple_viewer(), out, wait_ms=2000)
        assert os.path.getsize(out) > 10_000


class TestServe:
    def test_yields_url(self):
        viewer = _simple_viewer()
        with testing.serve(viewer) as url:
            assert url.startswith("http://127.0.0.1:")
            assert "/index.html" in url
