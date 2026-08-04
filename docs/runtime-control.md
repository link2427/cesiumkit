# How to control a live viewer from Python

_How-to. Target: a running `show()` viewer whose clock, data, and camera you
can change from the same Python process, and that can call back into
Python._

cesiumkit keeps a two-way bridge between Python and the browser. Python can
update the clock and data sources, select or pick entities, capture the
canvas, and receive click events without rebuilding the page.

## 1. Start a controllable viewer

`Viewer.show()` serves the page and blocks while the server runs. Start it
in a daemon thread when the same process needs to issue live commands:

```python
from threading import Thread
from time import sleep

import cesiumkit

viewer = cesiumkit.Viewer(title="Runtime control")

Thread(target=viewer.show, kwargs={"open_browser": True}, daemon=True).start()

# Give the browser time to load before requesting values from it.
sleep(1)
```

Commands that only update browser state can be queued before the page
loads. Methods that return browser state — `get_current_time()`, `pick()`,
the screenshot methods — require the page to be loaded.

## 2. Drive the clock

```python
viewer.set_time("2026-07-14T18:00:00Z")
viewer.set_multiplier(60)  # one simulated minute per real second
viewer.animate(True)

print(viewer.get_current_time())
viewer.animate(False)
```

## 3. Update live data

Replace the first matching CZML or GeoJSON source with a URL or an
in-memory JSON-compatible value:

```python
viewer.update_czml(
    [
        {"id": "document", "version": "1.0"},
        {"id": "vehicle", "position": {"cartographicDegrees": [-87.63, 41.88, 0]}},
    ]
)
viewer.update_geojson({"type": "FeatureCollection", "features": []})
```

For browser-side polling, keep the returned ID so the poller can be stopped:

```python
poller = viewer.poll_czml("https://example.com/live.czml", interval=5)
viewer.stop_polling(poller)
```

`stream_czml()` accepts any iterable of CZML packet batches and returns the
daemon thread sending them:

```python
stream = viewer.stream_czml(packet_batches, interval=1)
stream.join()
```

## 4. Select and pick entities

```python
viewer.select_entity("vehicle")
selected = viewer.selected_entity
viewer.deselect()

position = cesiumkit.Cartesian2(x=400, y=300)
frontmost = viewer.pick(position)
all_entities = viewer.drill_pick(position)
```

Picking returns local Python `Entity` objects when the IDs received from
Cesium match entities in this viewer.

## 5. Receive clicks in Python

Register callbacks before or after the server starts. Each callback
receives the clicked entity's public ID, or `None` for empty space:

```python
viewer.on_click(lambda entity_id: print("clicked:", entity_id))
```

For synchronous code, wait for the next click instead:

```python
try:
    entity_id = viewer.wait_for_click(timeout=30)
except TimeoutError:
    print("No click received")
```

Multiple callbacks are supported; an exception in one is logged without
stopping the others.

## 6. Capture the canvas

```python
viewer.screenshot("viewer.png")
png_base64 = viewer.screenshot_base64()
image = viewer.canvas_to_image()  # pip install "cesiumkit[images]"
```

Canvas capture follows browser CORS rules: remote imagery servers must
permit cross-origin canvas use or the browser rejects the readback.

See
[`examples/11_runtime_control.py`](https://github.com/link2427/cesiumkit/blob/main/examples/11_runtime_control.py)
for a complete runnable example.
