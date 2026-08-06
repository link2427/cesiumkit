"""Regression tests for benchmark sample construction."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _benchmark_script():
    path = Path(__file__).parents[1] / "scripts" / "benchmark.py"
    spec = importlib.util.spec_from_file_location("benchmark", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_throughput_tiles_are_distinct_and_valid() -> None:
    benchmark = _benchmark_script()
    tiles = benchmark._distinct_world_tiles(200, 4)
    assert len(tiles) == 200
    assert len(set(tiles)) == 200
    assert all(0 <= x < 1 << z and 0 <= y < 1 << z for z, x, y in tiles)
