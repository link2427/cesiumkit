#!/usr/bin/env python3
"""Render every runnable example headlessly and save PNGs.

Used by the CI ``render-check`` job to prove the examples still initialize
and render on the bundled Cesium build; the PNGs are uploaded as build
artifacts. Examples that never call ``viewer.show()`` (e.g. the CZML-export
and runtime-control ones) are skipped.

Requires:
    pip install "cesiumkit[gis]" playwright
    python -m playwright install chromium
    python scripts/fetch_cesium.py   # for offline serving

Usage:
    python scripts/render_examples.py [--output /tmp/cesiumkit-renders]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import cesiumkit
from cesiumkit import testing

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


def _load_example_viewer(path: Path):
    """Import an example module, capturing the viewer it calls show() on."""
    real_show = cesiumkit.Viewer.show
    captured: dict[str, object] = {}

    def fake_show(self, *args, **kwargs):
        captured["viewer"] = self
        return None

    cesiumkit.Viewer.show = fake_show
    try:
        module_name = f"render_example_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        cesiumkit.Viewer.show = real_show
    return captured.get("viewer")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/cesiumkit-renders", help="directory for PNG outputs")
    parser.add_argument("--wait-ms", type=int, default=testing.DEFAULT_WAIT_MS, help="load wait per example")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    examples = sorted(EXAMPLES_DIR.glob("[0-9][0-9]_*.py"))
    rendered: list[str] = []
    failures: list[str] = []
    for path in examples:
        source = path.read_text(encoding="utf-8")
        if "viewer.show()" not in source:
            print(f"skip {path.name}: not a show()-based example")
            continue
        try:
            viewer = _load_example_viewer(path)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append(f"{path.name}: {exc}")
            print(f"FAIL {path.name}: {exc}")
            continue
        if viewer is None:
            print(f"skip {path.name}: no viewer.show() call executed")
            continue
        out = output_dir / f"{path.stem}.png"
        try:
            testing.render_screenshot(viewer, str(out), wait_ms=args.wait_ms)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append(f"{path.name}: {exc}")
            print(f"FAIL {path.name}: {exc}")
            continue
        rendered.append(path.name)
        print(f"rendered {path.name} -> {out}")

    print(f"rendered {len(rendered)}/{len(examples)} examples")
    if failures:
        print("failures:")
        for failure in failures:
            print("  -", failure)
        return 1
    return 0 if rendered else 1


if __name__ == "__main__":
    sys.exit(main())
