"""Resource-cleanup regressions for the headless testing helpers."""

from contextlib import contextmanager

import pytest

from cesiumkit import testing


class _FakeBrowser:
    def __init__(self, page=None):
        self.page = page
        self.closed = False

    def new_page(self, **_kwargs):
        return self.page

    def close(self):
        self.closed = True


class _FakePlaywright:
    def __init__(self, browser):
        self._browser = browser
        self.chromium = self
        self.stopped = False

    def launch(self, **_kwargs):
        return self._browser

    def stop(self):
        self.stopped = True


def test_start_server_surfaces_show_failure():
    class Viewer:
        _server = None

        def show(self, **_kwargs):
            raise OSError("port unavailable")

        def close(self):
            pass

    with pytest.raises(RuntimeError, match="failed to start") as exc_info:
        testing.start_server(Viewer())

    assert isinstance(exc_info.value.__cause__, OSError)


def test_load_page_cleans_up_when_navigation_fails(monkeypatch):
    class Page:
        def on(self, *_args):
            pass

        def goto(self, *_args, **_kwargs):
            raise RuntimeError("navigation failed")

    browser = _FakeBrowser(Page())
    playwright = _FakePlaywright(browser)
    monkeypatch.setattr(testing, "_playwright", lambda: playwright)

    with pytest.raises(RuntimeError, match="navigation failed"):
        testing._load_page("http://example.invalid", viewport={"width": 1, "height": 1}, wait_ms=0)

    assert browser.closed
    assert playwright.stopped


@contextmanager
def _fake_serve(_viewer):
    yield "http://example.invalid"


def test_render_state_cleans_up_when_evaluation_fails(monkeypatch):
    class Page:
        def evaluate(self, *_args):
            raise RuntimeError("evaluation failed")

    browser = _FakeBrowser()
    playwright = _FakePlaywright(browser)
    monkeypatch.setattr(testing, "serve", _fake_serve)
    monkeypatch.setattr(testing, "_load_page", lambda *_args, **_kwargs: (Page(), [], browser, playwright))

    with pytest.raises(RuntimeError, match="evaluation failed"):
        testing.render_state(object(), wait_ms=0)

    assert browser.closed
    assert playwright.stopped


def test_render_screenshot_cleans_up_when_capture_fails(monkeypatch, tmp_path):
    class Page:
        def screenshot(self, **_kwargs):
            raise RuntimeError("capture failed")

    browser = _FakeBrowser()
    playwright = _FakePlaywright(browser)
    monkeypatch.setattr(testing, "serve", _fake_serve)
    monkeypatch.setattr(testing, "_load_page", lambda *_args, **_kwargs: (Page(), [], browser, playwright))

    with pytest.raises(RuntimeError, match="capture failed"):
        testing.render_screenshot(object(), str(tmp_path / "shot.png"), wait_ms=0)

    assert browser.closed
    assert playwright.stopped


def test_render_screenshot_reports_uncaught_page_errors(monkeypatch, tmp_path):
    class Page:
        def screenshot(self, **_kwargs):
            pass

    browser = _FakeBrowser()
    playwright = _FakePlaywright(browser)
    monkeypatch.setattr(testing, "serve", _fake_serve)
    monkeypatch.setattr(
        testing,
        "_load_page",
        lambda *_args, **_kwargs: (Page(), ["render exploded"], browser, playwright),
    )

    with pytest.raises(RuntimeError, match="render exploded"):
        testing.render_screenshot(object(), str(tmp_path / "shot.png"), wait_ms=0)

    assert browser.closed
    assert playwright.stopped
