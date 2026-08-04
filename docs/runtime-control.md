# Runtime control

cesiumkit 0.3 adds a two-way bridge between Python and a live Cesium viewer.
Python can update the clock and data sources, select or pick entities, capture
the canvas, and receive click events without rebuilding the page.

## Start a controllable viewer

`Viewer.show()` serves the generated page and blocks while the server is
running. Start it in a daemon thread when the same Python process needs to
issue live commands:

```python
from threading import Thread
from time import sleep

import cesiumkit

viewer = cesiumkit.Viewer(title="Runtime control")

server = Thread(
    target=viewer.show,
    kwargs={"open_browser": True},
    daemon=True,
)
server.start()

# Give the browser time to load before requesting values from it.
sleep(1)
```

Commands that only update browser state can be queued before the page loads.
Methods that return browser state, such as `get_current_time()`, `pick()`, and
the screenshot methods, require `show()` and the browser page to be running.

## Control the clock

```python
viewer.set_time("2026-07-14T18:00:00Z")
viewer.set_multiplier(60)  # one simulated minute per real second
viewer.animate(True)

print(viewer.get_current_time())
viewer.animate(False)
```

## Update live data

Replace the first matching CZML or GeoJSON source with a URL or an in-memory
JSON-compatible value:

```python
viewer.update_czml(
    [
        {"id": "document", "version": "1.0"},
        {"id": "vehicle", "position": {"cartographicDegrees": [-87.63, 41.88, 0]}},
    ]
)

viewer.update_geojson(
    {
        "type": "FeatureCollection",
        "features": [],
    }
)
```

For browser-side polling, keep the returned ID so the poller can be stopped:

```python
poller = viewer.poll_czml("https://example.com/live.czml", interval=5)
viewer.stop_polling(poller)
```

`stream_czml()` accepts any iterable of CZML packet batches and returns the
daemon thread that is sending them:

```python
stream = viewer.stream_czml(packet_batches, interval=1)
stream.join()
```

## Select and pick entities

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

## Receive clicks in Python

Register callbacks before or after the server starts. Each callback receives
the clicked entity's public ID, or `None` for empty space:

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

Multiple callbacks are supported. Exceptions raised by one callback are logged
without preventing the others from running.

## Capture the canvas

```python
viewer.screenshot("viewer.png")
png_base64 = viewer.screenshot_base64()
image = viewer.canvas_to_image()  # pip install "cesiumkit[images]"
```

Canvas capture is subject to normal browser CORS rules. Remote imagery servers
must permit cross-origin canvas use or the browser will reject the readback.

See [`examples/11_runtime_control.py`](https://github.com/link2427/cesiumkit/blob/main/examples/11_runtime_control.py)
for a complete runnable example.
