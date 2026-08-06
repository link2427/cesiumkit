#!/usr/bin/env python3
"""Headless render smoke test (thin CLI wrapper over cesiumkit.testing).

Loads a viewer page in headless Chromium and verifies the globe actually
initializes and renders. Used to validate the bundled (offline) Cesium build
end to end.

Requires:
    pip install "cesiumkit[testing]"
    python -m playwright install chromium

Usage:
    python scripts/smoke_render.py [--screenshot /tmp/smoke.png]
"""

from __future__ import annotations

import argparse
import sys

import cesiumkit
from cesiumkit import testing
from cesiumkit._vendor import vendor_dir


def _smoke_viewer() -> cesiumkit.Viewer:
    """Create the deterministic scene used by each independent smoke pass."""
    viewer = cesiumkit.Viewer(title="Smoke test")
    viewer.add_entity(
        cesiumkit.Entity(
            name="NYC",
            position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
            point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
        )
    )
    viewer.add_entity(
        cesiumkit.Entity(
            name="SF",
            position=cesiumkit.Cartesian3.from_degrees(-122.42, 37.77, 400),
            label=cesiumkit.LabelGraphics(text="SF", pixel_offset=cesiumkit.Cartesian2(x=0, y=-24)),
        )
    )
    return viewer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", default=None, help="path to save a PNG screenshot")
    args = parser.parse_args()

    if args.screenshot:
        testing.render_screenshot(_smoke_viewer(), args.screenshot)
        import os

        print(f"screenshot: {args.screenshot} ({os.path.getsize(args.screenshot)} bytes)")

    vendor = vendor_dir()
    if vendor is None:
        print("FAIL: the installed package has no vendored Cesium build")
        return 1

    state = testing.render_state(_smoke_viewer(), wait_ms=10_000)
    print(f"state: {state}")
    if not state.get("ok"):
        print("FAIL: viewer did not initialize")
        return 1
    if state.get("cesiumScript") != "/vendor/cesium/Cesium.js":
        print("FAIL: viewer did not load Cesium from the vendored build")
        return 1
    if not state.get("tilesLoaded"):
        print("FAIL: vendored imagery tiles did not finish loading")
        return 1
    if state.get("pageErrors"):
        print("FAIL: uncaught page errors:")
        for err in state["pageErrors"]:
            print("  -", err)
        return 1
    print(f"OK: rendered with vendored Cesium from {vendor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
