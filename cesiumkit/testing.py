"""Headless rendering helpers for tests and CI (optional ``playwright`` dep).

These helpers start the local viewer server, load the page in headless
Chromium, and let you assert on render state or save screenshots. Each helper
closes its viewer when finished; create an equivalent fresh viewer for a
second render. They are what ``scripts/render_examples.py`` uses in CI and for
the docs gallery.

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
    errors: list[BaseException] = []

    def run() -> None:
        try:
            viewer.show(port=port, open_browser=False)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    for _ in range(200):
        if viewer._server is not None:
            return viewer._server
        if errors:
            raise RuntimeError("viewer server failed to start") from errors[0]
        if not thread.is_alive():
            break
        time.sleep(0.05)
    viewer.close()
    thread.join(timeout=1)
    raise RuntimeError("viewer server did not start")


@contextmanager
def serve(viewer: Any, port: int = 0) -> Iterator[str]:
    """Context manager yielding the served URL of a viewer."""
    server = start_server(viewer, port=port)
    url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    try:
        yield url
    finally:
        viewer.close()


def _load_page(url: str, *, viewport: dict[str, int], wait_ms: int):
    """Load a page and return its page, errors, browser, and Playwright owner."""
    playwright = _playwright()
    browser = None
    try:
        browser = playwright.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
        errors: list[str] = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, wait_until="load")
        page.wait_for_timeout(wait_ms)
        return page, errors, browser, playwright
    except BaseException:
        try:
            if browser is not None:
                browser.close()
        finally:
            playwright.stop()
        raise


def render_state(
    viewer: Any,
    *,
    wait_ms: int = DEFAULT_WAIT_MS,
    viewport: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Load the viewer headlessly and report how the scene initialized.

    Closes ``viewer`` before returning. Returns a dict with ``ok`` (viewer + globe initialized), ``tilesLoaded``,
    ``imageryLayers``, ``cesiumScript`` (the script URL as written in the
    page), and ``pageErrors`` (uncaught JS exceptions).
    """
    viewport = viewport or DEFAULT_VIEWPORT
    with serve(viewer) as url:
        page, errors, browser, playwright = _load_page(url, viewport=viewport, wait_ms=wait_ms)
        try:
            state = page.evaluate(
                """() => {
                    const v = window.viewer;
                    if (!v || !v.scene || !v.scene.globe) return {ok: false};
                    return {
                        ok: true,
                        tilesLoaded: v.scene.globe.tilesLoaded,
                        imageryLayers: v.imageryLayers.length,
                        cesiumScript: document.querySelector('script[src*="Cesium.js"]')?.getAttribute('src'),
                    };
                }"""
            )
        finally:
            try:
                browser.close()
            finally:
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
    """Load the viewer, save a PNG screenshot to ``path``, then close it."""
    viewport = viewport or DEFAULT_VIEWPORT
    with serve(viewer) as url:
        page, errors, browser, playwright = _load_page(url, viewport=viewport, wait_ms=wait_ms)
        try:
            page.screenshot(path=path, full_page=False, timeout=screenshot_timeout_ms)
        finally:
            try:
                browser.close()
            finally:
                playwright.stop()
    if errors:
        raise RuntimeError(f"viewer page raised uncaught JavaScript errors: {'; '.join(errors)}")
    return path


__all__ = [
    "DEFAULT_VIEWPORT",
    "DEFAULT_WAIT_MS",
    "render_screenshot",
    "render_state",
    "serve",
    "start_server",
]
