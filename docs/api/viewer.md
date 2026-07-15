# Viewer

The main entry point for building CesiumJS visualizations.

::: cesiumkit.viewer

## Runtime clock control

When a viewer is being served with `show()`, Python can update and read its
live Cesium clock:

```python
viewer.set_time("2024-03-15T03:00:00Z")
viewer.animate(on=True)
viewer.set_multiplier(60)
current_time = viewer.get_current_time()
```

`show()` blocks while serving. Run it in a background thread when the same
Python process needs to issue runtime commands.
