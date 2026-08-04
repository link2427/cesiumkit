"""Headless rendering helpers for tests and CI (optional ``playwright`` dep).

These helpers start the local viewer server, load the page in headless
Chromium, and let you assert on render state or save screenshots. They are
the library-side equivalent of what ``scripts/generate_gallery.py`` does for
the gallery, and are what ``scripts/render_examples.py`` uses in CI.

Playwright is imported lazily, so ``import cesiumkit.testing`` is cheap even
when it is not installed.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
DEFAULT_WAIT_MS = 6000


def _playwright():
    from playwright.sync_api import sync_playwright

    return sync_playwright().start()


def start_server(viewer: Any, port: int = 0) -> Any:
    """Start ``viewer.show()`` in a background thread and return the server.

    Raises ``RuntimeError`` if the server does not come up within ~10s.
    """
    thread = threading.Thread(
        target=viewer.show,
        kwargs={"port": port, "open_browser": False},
        daemon=True,
    )
    thread.start()
    for _ in range(200):
        if viewer._server is not None:
            return viewer._server
        time.sleep(0.05)
    raise RuntimeError("viewer server did not start")


@contextmanager
def serve(viewer: Any, port: int = 0) -> Iterator[str]:
    """Context manager yielding the served URL of a viewer."""
    server = start_server(viewer, port=port)
    url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()


def _load_page(url: str, *, viewport: dict[str, int], wait_ms: int):
    """Load a page, collect page errors, and return (page, errors, browser)."""
    playwright = _playwright()
    browser = playwright.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport=viewport)
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(url, wait_until="load")
    page.wait_for_timeout(wait_ms)
    return page, errors, browser, playwright


def render_state(
    viewer: Any,
    *,
    wait_ms: int = DEFAULT_WAIT_MS,
    viewport: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Load the viewer headlessly and report how the scene initialized.

    Returns a dict with ``ok`` (viewer + globe initialized), ``tilesLoaded``,
    ``imageryLayers``, and ``pageErrors`` (uncaught JS exceptions).
    """
    viewport = viewport or DEFAULT_VIEWPORT
    with serve(viewer) as url:
        page, errors, browser, playwright = _load_page(url, viewport=viewport, wait_ms=wait_ms)
        state = page.evaluate(
            """() => {
                const v = window.viewer;
                if (!v || !v.scene || !v.scene.globe) return {ok: false};
                return {
                    ok: true,
                    tilesLoaded: v.scene.globe.tilesLoaded,
                    imageryLayers: v.imageryLayers.length,
                };
            }"""
        )
        browser.close()
        playwright.stop()
    state["pageErrors"] = errors
    return state


def render_screenshot(
    viewer: Any,
    path: str,
    *,
    wait_ms: int = DEFAULT_WAIT_MS,
    viewport: dict[str, int] | None = None,
    screenshot_timeout_ms: int = 60_000,
) -> str:
    """Load the viewer headlessly and save a PNG screenshot to ``path``."""
    viewport = viewport or DEFAULT_VIEWPORT
    with serve(viewer) as url:
        page, _errors, browser, playwright = _load_page(url, viewport=viewport, wait_ms=wait_ms)
        page.screenshot(path=path, full_page=False, timeout=screenshot_timeout_ms)
        browser.close()
        playwright.stop()
    return path


__all__ = [
    "DEFAULT_VIEWPORT",
    "DEFAULT_WAIT_MS",
    "render_screenshot",
    "render_state",
    "serve",
    "start_server",
]
