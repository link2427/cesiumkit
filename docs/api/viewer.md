# Viewer

The main entry point for building CesiumJS visualizations.

::: cesiumkit.viewer

## Shadows and 3D-only mode

`shadows` and `terrain_shadows` take a `ShadowMode` (`DISABLED`, `ENABLED`,
`CAST_ONLY`, `RECEIVE_ONLY`) and control which objects cast and receive
shadows. `scene3d_only=True` builds a scene that only ever renders in 3D
(no 2D/Columbus morphing widgets, marginally faster startup):

```python
viewer = cesiumkit.Viewer(
    shadows=cesiumkit.ShadowMode.ENABLED,
    terrain_shadows=cesiumkit.ShadowMode.RECEIVE_ONLY,
    scene3d_only=False,
)
```

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

## Live data sources

CZML and GeoJSON sources can be replaced without rebuilding the viewer. Values
may be URLs or in-memory JSON-compatible data:

```python
viewer.update_czml([{"id": "document", "version": "1.0"}, packet])
viewer.update_geojson({"type": "FeatureCollection", "features": []})

poller = viewer.poll_czml("https://example.com/live.czml", interval=5)
viewer.stop_polling(poller)
```

For Python-produced updates, `stream_czml()` consumes an iterable of CZML
packet batches in a daemon thread.

## Runtime selection and picking

Selection commands operate on entities already added to the viewer. Picking
returns the corresponding local Python `Entity` when its ID is known:

```python
viewer.select_entity("sat-1")
selected = viewer.selected_entity
picked = viewer.pick(cesiumkit.Cartesian2(x=100, y=200))
all_picked = viewer.drill_pick(cesiumkit.Cartesian2(x=100, y=200))
viewer.deselect()
```

## Python click events

Register callbacks before or after `show()` starts, or synchronously wait for
the next click. A click on an entity returns its public ID; a click on empty
space returns `None`:

```python
viewer.on_click(lambda entity_id: print("clicked", entity_id))

# Run viewer.show() in another thread, then:
entity_id = viewer.wait_for_click(timeout=30)
```

`wait_for_click()` raises `TimeoutError` when no click arrives before the
timeout. Callback exceptions are logged and do not prevent other callbacks
from running.

## Screenshots

Capture the live canvas as a file, base64 text, or a Pillow image:

```python
viewer.screenshot("output.png")
encoded = viewer.screenshot_base64()
image = viewer.canvas_to_image()  # pip install cesiumkit[images]
```
