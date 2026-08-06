"""Regression tests for the release browser-smoke CLI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _smoke_script():
    path = Path(__file__).parents[1] / "scripts" / "smoke_render.py"
    spec = importlib.util.spec_from_file_location("smoke_render", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_screenshot_and_state_use_distinct_terminal_viewers(monkeypatch, tmp_path) -> None:
    smoke_render = _smoke_script()
    viewers = []
    output = tmp_path / "smoke.png"

    def render_screenshot(viewer, path: str) -> str:
        viewers.append(viewer)
        Path(path).write_bytes(b"png")
        return path

    def render_state(viewer, **_kwargs):
        viewers.append(viewer)
        return {
            "ok": True,
            "tilesLoaded": True,
            "cesiumScript": "/vendor/cesium/Cesium.js",
            "pageErrors": [],
        }

    monkeypatch.setattr(smoke_render.testing, "render_screenshot", render_screenshot)
    monkeypatch.setattr(smoke_render.testing, "render_state", render_state)
    monkeypatch.setattr(smoke_render, "vendor_dir", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["smoke_render.py", "--screenshot", str(output)])

    assert smoke_render.main() == 0
    assert len(viewers) == 2
    assert viewers[0] is not viewers[1]
    assert viewers[0].to_html() == viewers[1].to_html()
