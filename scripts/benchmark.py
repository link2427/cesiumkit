#!/usr/bin/env python3
"""Rough performance sanity checks. Not CI-gated (timing is noisy).

Measures:
- Viewer.to_html() time at 1k / 10k / 50k entities
- Raster tile latency: first render vs cached hit

Run:  python scripts/benchmark.py
"""

from __future__ import annotations

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


def main() -> int:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
