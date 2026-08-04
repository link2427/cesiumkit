#!/usr/bin/env python3
"""Headless render smoke test.

Loads a viewer page in headless Chromium and verifies the globe actually
initializes and renders tiles. Used to validate the bundled (offline) Cesium
build end to end; mirrors what the gallery workflow does for screenshots.

Requires:
    pip install playwright
    python -m playwright install chromium

Usage:
    python scripts/smoke_render.py [--screenshot /tmp/smoke.png]
"""

from __future__ import annotations

import argparse
import sys
import threading
import time

import cesiumkit

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sys.exit("playwright is not installed; run: pip install playwright && python -m playwright install chromium")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", default=None, help="path to save a PNG screenshot")
    args = parser.parse_args()

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

    thread = threading.Thread(
        target=viewer.show,
        kwargs={"port": 0, "open_browser": False},
        daemon=True,
    )
    thread.start()
    for _ in range(200):
        if viewer._server is not None:
            break
        time.sleep(0.05)
    else:
        print("FAIL: server did not start")
        return 1
    url = f"http://127.0.0.1:{viewer._server.server_address[1]}/index.html"

    page_errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.goto(url, wait_until="load")
        page.wait_for_timeout(6000)  # let the first tiles load

        state = page.evaluate(
            """() => {
                const v = window.viewer;
                if (!v || !v.scene || !v.scene.globe) return {ok: false};
                return {
                    ok: true,
                    tilesLoaded: v.scene.globe.tilesLoaded,
                    imageryLayers: v.imageryLayers.length,
                    terrainProvider: v.scene.terrainProvider.constructor.name,
                    cesiumVersion: typeof v.cesiumWidget !== 'undefined' ? 'n/a' : 'n/a',
                };
            }"""
        )
        if args.screenshot:
            page.screenshot(path=args.screenshot, full_page=False)
        browser.close()

    print(f"state: {state}")
    if args.screenshot:
        import os

        print(f"screenshot: {args.screenshot} ({os.path.getsize(args.screenshot)} bytes)")
    if page_errors:
        print("page errors:")
        for err in page_errors:
            print("  -", err)

    if not state.get("ok"):
        print("FAIL: viewer did not initialize")
        return 1
    if page_errors:
        print("FAIL: uncaught page errors")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
