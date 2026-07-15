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
