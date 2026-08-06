#!/usr/bin/env python3
"""Repeatable local performance probes. They are not CI-gated.

Measures:
- ``Viewer.to_html()`` for 1k / 10k / 50k prebuilt entities
- Raster tile latency (cold versus cached) and cold-cache throughput across
  distinct, valid tiles
- Optional browser navigation plus a fixed settle period (needs the bundled
  build and ``cesiumkit[testing]``): ``python scripts/benchmark.py --render``

The output is a local measurement, not a release performance promise. Record
the Python version, platform, dependency versions, and command line alongside
any result you compare or publish.
"""

from __future__ import annotations

import argparse
import statistics
import tempfile
import time
from pathlib import Path

import cesiumkit

SERIALIZATION_REPEATS = 5
RASTER_LATENCY_REPEATS = 10
THROUGHPUT_ROUNDS = 5
THROUGHPUT_ZOOM = 4
THROUGHPUT_TILE_COUNT = 200
WEB_MERCATOR_LIMIT = 20_037_508.342789244


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


def _median_ms(samples: list[float]) -> float:
    return statistics.median(samples) * 1000


def _distinct_world_tiles(count: int, zoom: int) -> list[tuple[int, int, int]]:
    """Return distinct valid Web Mercator tile coordinates at one zoom level."""
    side = 1 << zoom
    if count > side * side:
        raise ValueError(f"cannot choose {count} unique tiles at zoom {zoom}")
    return [(zoom, index % side, index // side) for index in range(count)]


def _raster_benchmark() -> None:
    try:
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        print('== raster benchmarks skipped: install "cesiumkit[raster]" ==')
        return

    with tempfile.TemporaryDirectory(prefix="cesiumkit-benchmark-") as tmpdir:
        tmp = Path(tmpdir) / "bench.tif"
        pixels = np.zeros((3, 256, 256), dtype="uint8")
        pixels[0, ...] = 255
        with rasterio.open(
            tmp,
            "w",
            driver="GTiff",
            height=256,
            width=256,
            count=3,
            dtype="uint8",
            crs="EPSG:3857",
            transform=from_bounds(
                -WEB_MERCATOR_LIMIT,
                -WEB_MERCATOR_LIMIT,
                WEB_MERCATOR_LIMIT,
                WEB_MERCATOR_LIMIT,
                256,
                256,
            ),
        ) as dst:
            dst.write(pixels)
        source = _raster_source(str(tmp))

        print("== raster tile latency (same valid tile; cache cleared before each cold sample) ==")
        cold_samples = []
        for _ in range(RASTER_LATENCY_REPEATS):
            source.clear_cache()
            start = time.perf_counter()
            assert source.tile(0, 0, 0) is not None
            cold_samples.append(time.perf_counter() - start)
        start = time.perf_counter()
        assert source.tile(0, 0, 0) is not None
        cached = time.perf_counter() - start
        print(f"  cold render median: {_median_ms(cold_samples):.1f} ms")
        print(f"  cached hit:         {cached * 1000:.2f} ms")

        tiles = _distinct_world_tiles(THROUGHPUT_TILE_COUNT, THROUGHPUT_ZOOM)
        assert len(set(tiles)) == len(tiles)
        throughput_samples = []
        for _ in range(THROUGHPUT_ROUNDS):
            source.clear_cache()
            start = time.perf_counter()
            for z, x, y in tiles:
                assert source.tile(z, x, y) is not None
            throughput_samples.append(time.perf_counter() - start)
        median_seconds = statistics.median(throughput_samples)
        print(
            "== raster throughput "
            f"({len(tiles)} distinct z{THROUGHPUT_ZOOM} tiles; {THROUGHPUT_ROUNDS} cold-cache rounds) =="
        )
        print(f"  median: {len(tiles) / median_seconds:.0f} tiles/s ({median_seconds:.2f}s per round)")


def _render_timing() -> None:
    """Measure navigation plus a fixed settle period in headless Chromium."""
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
        print(f"  {count:>6,} entities: navigation + fixed 3s settle in {elapsed:.1f}s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="also time headless browser navigation")
    args = parser.parse_args()

    print("== to_html() at scale (median of five serializations; viewer construction excluded) ==")
    for count in (1_000, 10_000, 50_000):
        viewer = _viewer_with_points(count)
        samples = []
        html = ""
        for _ in range(SERIALIZATION_REPEATS):
            start = time.perf_counter()
            html = viewer.to_html()
            samples.append(time.perf_counter() - start)
        print(f"  {count:>6,} entities: {_median_ms(samples):.1f} ms median ({len(html) / 1e6:.1f} MB html)")

    _raster_benchmark()

    if args.render:
        print("== headless browser navigation ==")
        _render_timing()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
