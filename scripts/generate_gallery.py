"""Generate gallery screenshots using playwright.

Imports each ``scripts/gallery/NN_<name>.py`` module, grabs its module-level
``viewer`` object, writes the HTML to a temp file, loads it in a headless
browser, waits for Cesium to finish loading tiles, and screenshots the canvas.

Run locally:

    pip install cesiumkit[gis] playwright
    python -m playwright install chromium
    python scripts/generate_gallery.py

In CI this is invoked by ``.github/workflows/gallery.yml``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError as e:
    raise SystemExit(
        "playwright is not installed. Run:\n  pip install playwright\n  python -m playwright install chromium"
    ) from e

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = REPO_ROOT / "scripts" / "gallery"
OUTPUT_DIR = REPO_ROOT / "docs" / "images" / "gallery"

# 16:9 viewport used for all gallery shots -- matches the README grid layout.
VIEWPORT = {"width": 1600, "height": 900}

# Max time to wait for Cesium to report that all imagery tiles have loaded.
TILE_LOAD_TIMEOUT_MS = 30_000

# Pin the gallery to Cesium 1.105. Cesium 1.106+ has a bug where its bundled
# DOMPurify init crashes in headless chromium with "Cannot read properties of
# null (reading 'createElement')", which breaks the imagery tile loader --
# tiles get queued but never fetched, so the globe renders as a black sphere
# against the skybox. 1.105 is the last release that works reliably headless.
# The library itself still defaults to the latest Cesium for real-browser users;
# this pin only applies to gallery screenshots.
CESIUM_VERSION_FOR_SCREENSHOTS = "1.105"


def _load_gallery_module(path: Path):
    """Import a gallery script as a module, without it being on sys.path."""
    module_name = f"gallery_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _wait_for_cesium_ready(page) -> None:
    """Block until Cesium has finished loading its imagery tiles.

    ``globe.tilesLoaded`` returns true whenever the three tile load queues are
    empty, which is trivially the case at t=0 before Cesium has queued anything.
    So require an initial false state (real tiles entered the queue) before we
    start trusting tilesLoaded=true as meaningful.
    """
    js = f"""
    () => new Promise(resolve => {{
        const start = Date.now();
        let sawLoading = false;
        const check = () => {{
            const v = window.viewer;
            const globe = v && v.scene && v.scene.globe;
            if (globe) {{
                if (!globe.tilesLoaded) {{
                    sawLoading = true;
                }} else if (sawLoading) {{
                    requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)));
                    return;
                }}
            }}
            if (Date.now() - start > {TILE_LOAD_TIMEOUT_MS}) {{ resolve(false); return; }}
            setTimeout(check, 100);
        }};
        check();
    }})
    """
    try:
        page.evaluate(js)
    except Exception:
        pass
    # Extra settle for any final render / camera easing.
    page.wait_for_timeout(1000)


def _screenshot_viewer(viewer, out_path: Path) -> None:
    """Render viewer to HTML and screenshot it with playwright."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Pin to a Cesium version that works in headless chromium. See the module
    # constant's docstring for why.
    viewer.cesium_version = CESIUM_VERSION_FOR_SCREENSHOTS

    with tempfile.TemporaryDirectory(prefix="cesiumkit_gallery_") as tmpdir:
        html_path = os.path.join(tmpdir, "index.html")
        viewer.save(html_path)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()
            page.on("pageerror", lambda err: print(f"    [pageerror] {err}"))

            page.goto(f"file://{html_path}")
            _wait_for_cesium_ready(page)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()


def main() -> int:
    # Force the no-Ion path in the viewer template so we render NaturalEarthII
    # (bundled with CesiumJS, no auth needed) instead of World Imagery (which
    # needs a valid Ion asset token and silently fails if the token is wrong).
    os.environ.pop("CESIUM_ION_TOKEN", None)

    if not GALLERY_DIR.exists():
        print(f"Gallery directory not found: {GALLERY_DIR}", file=sys.stderr)
        return 1

    scripts = sorted(p for p in GALLERY_DIR.glob("*.py") if not p.name.startswith("_"))
    if not scripts:
        print(f"No gallery scripts found in {GALLERY_DIR}", file=sys.stderr)
        return 1

    print(f"Found {len(scripts)} gallery script(s)")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str]] = []
    for script in scripts:
        out_path = OUTPUT_DIR / f"{script.stem}.png"
        print(f"  {script.name} -> {out_path.relative_to(REPO_ROOT)}")
        try:
            module = _load_gallery_module(script)
            viewer = getattr(module, "viewer", None)
            if viewer is None:
                failures.append((script.name, "no module-level 'viewer'"))
                continue
            _screenshot_viewer(viewer, out_path)
        except Exception as e:
            failures.append((script.name, str(e)))
            print(f"    ERROR: {e}", file=sys.stderr)

    if failures:
        print(f"\n{len(failures)} failure(s):", file=sys.stderr)
        for name, err in failures:
            print(f"  - {name}: {err}", file=sys.stderr)
        return 1

    print(f"\nDone. Images in {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
