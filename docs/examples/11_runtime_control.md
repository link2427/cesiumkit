# Control a running viewer from Python

_Example — Starts `show()` in a thread, drives the clock, and receives click callbacks._

```python
"""Control a running viewer and receive entity clicks in Python."""

from threading import Thread
from time import sleep

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Runtime Control",
    animation=True,
    timeline=True,
)

viewer.add_entity(
    cesiumkit.Entity(
        id="chicago",
        name="Chicago",
        position=cesiumkit.Cartesian3.from_degrees(-87.6298, 41.8781, 0),
        point=cesiumkit.PointGraphics(
            pixel_size=16,
            color=cesiumkit.Color.DODGERBLUE,
            outline_color=cesiumkit.Color.WHITE,
            outline_width=2,
        ),
        label=cesiumkit.LabelGraphics(
            text="Click me",
            pixel_offset=cesiumkit.Cartesian2(x=0, y=-24),
        ),
    )
)


def report_click(entity_id: str | None) -> None:
    print("Clicked:", entity_id or "empty space")


# Register before show() so the click bridge is in the initial page.
viewer.on_click(report_click)
viewer.fly_to(cesiumkit.Cartesian3.from_degrees(-87.6298, 41.8781, 1_500_000))

# show() blocks, so run it in the background while Python controls the page.
server = Thread(target=viewer.show, kwargs={"open_browser": True}, daemon=True)
server.start()
sleep(1)

viewer.set_time("2026-07-14T18:00:00Z")
viewer.set_multiplier(60)
viewer.animate(True)
viewer.select_entity("chicago")

print("Live Cesium time:", viewer.get_current_time())
print("Click the globe. Press Ctrl+C to exit.")

try:
    while True:
        viewer.wait_for_click(timeout=None)
except KeyboardInterrupt:
    pass
```

Run it:

```bash
python examples/11_runtime_control.py
# Opens in browser — Ctrl+C to stop the server
```
