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

# 16:9 viewport used for all gallery shots — matches the README grid layout
VIEWPORT = {"width": 1600, "height": 900}

# Max time to wait for Cesium to report that all imagery tiles have loaded.
# If tiles don't finish (e.g. offline / slow tile server) we fall back to a
# fixed timeout so the CI job doesn't hang forever. First-time Cesium loads
# have to fetch the whole CDN bundle, plus we now wait for multi-pass tile
# loading to stabilize, so be generous.
TILE_LOAD_TIMEOUT_MS = 45_000


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

    Two subtleties here:

    1. ``globe.tilesLoaded`` returns true whenever the three tile load queues
       are empty, which is trivially the case at t=0 before Cesium has queued
       anything. So we require an initial false state (real tiles entered the
       queue) before we start trusting tilesLoaded=true as meaningful.

    2. Cesium loads tiles in multiple passes (low-res first, then progressively
       higher-res as the view stabilizes). A single false->true transition can
       fire after only the first pass, while the high-res pass is still pending.
       So instead of resolving on the first drain, we require
       ``STABLE_LOADED_MS`` milliseconds of *continuously* tilesLoaded=true --
       meaning no new tiles have entered the queue for that long.
    """
    js = f"""
    () => new Promise(resolve => {{
        const start = Date.now();
        let sawLoading = false;
        let loadedSince = 0;
        const STABLE_LOADED_MS = 2000;
        const check = () => {{
            const v = window.viewer;
            const globe = v && v.scene && v.scene.globe;
            if (globe) {{
                if (!globe.tilesLoaded) {{
                    sawLoading = true;
                    loadedSince = 0;
                }} else if (sawLoading) {{
                    if (loadedSince === 0) {{
                        loadedSince = Date.now();
                    }} else if (Date.now() - loadedSince > STABLE_LOADED_MS) {{
                        requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)));
                        return;
                    }}
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


_DIAGNOSTIC_JS = """
() => {
    const out = { hasViewer: !!window.viewer };
    const v = window.viewer;
    if (!v) return out;
    out.hasScene = !!v.scene;
    const globe = v.scene && v.scene.globe;
    if (!globe) return out;
    out.tilesLoaded = globe.tilesLoaded;
    out.baseColor = globe.baseColor && globe.baseColor.toCssColorString();
    const layers = globe.imageryLayers;
    out.layerCount = layers.length;
    out.layers = [];
    for (let i = 0; i < layers.length; i++) {
        const l = layers.get(i);
        const p = l.imageryProvider;
        out.layers.push({
            show: l.show,
            alpha: l.alpha,
            hasProvider: !!p,
            providerCtor: p && p.constructor && p.constructor.name,
            providerReady: p && (p.ready !== undefined ? p.ready : "n/a"),
            tilingScheme: p && p._tilingScheme && p._tilingScheme.constructor.name,
        });
    }
    return out;
}
"""


def _screenshot_viewer(viewer, out_path: Path) -> None:
    """Render viewer to HTML and screenshot it with playwright."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cesiumkit_gallery_") as tmpdir:
        html_path = os.path.join(tmpdir, "index.html")
        viewer.save(html_path)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()

            # Diagnostic plumbing: surface any browser-side console errors or
            # unhandled exceptions into the workflow log so we can see what's
            # actually breaking inside the headless chromium page.
            page.on(
                "console",
                lambda msg: print(f"    [browser.{msg.type}] {msg.text}"),
            )
            page.on("pageerror", lambda err: print(f"    [pageerror] {err}"))
            page.on(
                "requestfailed",
                lambda req: print(f"    [requestfailed] {req.url} -- {req.failure}"),
            )

            page.goto(f"file://{html_path}")
            _wait_for_cesium_ready(page)

            try:
                state = page.evaluate(_DIAGNOSTIC_JS)
                print(f"    [state] {state}")
            except Exception as e:
                print(f"    [state] evaluate failed: {e}")

            page.screenshot(path=str(out_path), full_page=False)
            browser.close()


def main() -> int:
    # Force the NaturalEarthII fallback path in the viewer template. Cesium's
    # default World Imagery (used when an Ion token is set) requires the token
    # to have access to the specific Ion asset -- if it doesn't, tile requests
    # silently return empty tiles and the globe renders as a black sphere
    # against the black skybox, which is exactly the failure mode we've been
    # chasing. NaturalEarthII is bundled with CesiumJS, needs no auth, and
    # always renders. To opt back into World Imagery later, remove this line
    # and ensure CESIUM_ION_TOKEN has the right asset permissions.
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
