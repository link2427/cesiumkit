# Headless Testing

Playwright-based helpers for rendering and screenshotting viewers without a
display. Used by the CI `render-check` job and available for local
verification.

```bash
pip install "cesiumkit[testing]"
python -m playwright install chromium
```

The render helpers close the viewer when each render finishes. Construct a
fresh equivalent `Viewer` when a test needs both a screenshot and render
state.

::: cesiumkit.testing
