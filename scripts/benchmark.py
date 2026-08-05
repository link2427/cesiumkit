#!/usr/bin/env python3
"""Rough performance sanity checks. Not CI-gated (timing is noisy).

Measures:
- Viewer.to_html() time at 1k / 10k / 50k entities
- Raster tile latency: first render vs cached hit, plus throughput
  across distinct tiles
- Optional headless page-load timing (needs the bundled build +
  playwright):  python scripts/benchmark.py --render

Run:  python scripts/benchmark.py
"""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

import cesiumkit


def _viewer_with_points(count: int) -> cesiumkit.Viewer:
    viewer = cesiumkit.Viewer()
    for i in range(count):
        lon = (i % 360) - 180
        lat = ((i // 360) % 180) - 90
        viewer.add_entity(
            cesiumkit.Entity(
                position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
                point=cesiumkit.PointGraphics(pixel_size=2),
            )
        )
    return viewer


def _raster_source(path: str) -> object:
    return __import__("cesiumkit.raster", fromlist=["RasterSource"]).RasterSource(path)


def _render_timing() -> None:
    """Headless page-load timing; requires the bundled build and playwright."""
    from cesiumkit import _vendor

    if _vendor.vendor_dir() is None:
        print("  (skipped: bundled Cesium build not present; run scripts/fetch_cesium.py)")
        return

    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print("  (skipped: playwright not installed)")
        return
    from cesiumkit.testing import serve

    for count in (1_000, 50_000):
        viewer = _viewer_with_points(count)
        with serve(viewer) as url:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1400, "height": 800})
                start = time.perf_counter()
                page.goto(url, wait_until="load")
                page.wait_for_timeout(3000)
                elapsed = time.perf_counter() - start
                browser.close()
        print(f"  {count:>6,} entities: page load + 3s settle in {elapsed:.1f}s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="also time headless page loads")
    args = parser.parse_args()

    print("== to_html() at scale ==")
    for count in (1_000, 10_000, 50_000):
        viewer = _viewer_with_points(count)
        start = time.perf_counter()
        html = viewer.to_html()
        elapsed = time.perf_counter() - start
        print(f"  {count:>6,} entities: {elapsed:.2f}s ({len(html) / 1e6:.1f} MB html)")

    print("== raster tile latency ==")
    tmp = Path(tempfile.mkdtemp()) / "bench.tif"
    pixels = np.zeros((3, 64, 64), dtype="uint8")
    pixels[0, ...] = 255
    with rasterio.open(
        tmp,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=3,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_bounds(-10, -10, 10, 10, 64, 64),
    ) as dst:
        dst.write(pixels)
    source = _raster_source(str(tmp))
    source.tile(0, 0, 0)  # warm the reader
    source.clear_cache()
    renders = []
    for _ in range(10):
        source.clear_cache()  # each round measures a real render
        start = time.perf_counter()
        source.tile(0, 0, 0)
        renders.append(time.perf_counter() - start)
    start = time.perf_counter()
    source.tile(0, 0, 0)
    cached = time.perf_counter() - start
    avg_render = sum(renders) / len(renders)
    print(f"  avg render (cache cleared): {avg_render * 1000:.1f} ms")
    print(f"  cached hit:                 {cached * 1000:.2f} ms")

    print("== raster throughput (distinct tiles) ==")
    source.clear_cache()
    total = 200
    start = time.perf_counter()
    for i in range(total):
        z, x, y = i % 5, (i * 7) % 32, (i * 13) % 32
        source.tile(z, x, y)
    elapsed = time.perf_counter() - start
    print(f"  {total} distinct tiles in {elapsed:.2f}s ({total / elapsed:.0f} tiles/s)")

    if args.render:
        print("== headless page load ==")
        _render_timing()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
