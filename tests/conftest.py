"""Shared pytest fixtures."""

import pytest


@pytest.fixture()
def playwright_browser():
    """A headless Chromium browser, or skip if playwright is unavailable."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            yield browser
        finally:
            browser.close()
