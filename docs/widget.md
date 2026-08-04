# Jupyter Widget

Render a viewer inside a notebook with live bidirectional control: set the
clock, receive click events, capture screenshots — no HTTP server required.

```bash
pip install "cesiumkit[widget]"
```

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_entity(cesiumkit.Entity(name="NYC", position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400)))

widget = viewer.to_widget()  # display this cell to render the globe
```

The widget loads CesiumJS from the CDN (notebooks have no local server), then
mirrors the runtime control API of `show()`:

```python
widget.set_time("2026-07-14T18:00:00Z")
widget.set_multiplier(60)
widget.animate(True)
widget.on_click(lambda entity_id: print("clicked", entity_id))
widget.screenshot("globe.png")
```

`widget.get_current_time()` reads the live clock back from the browser.

::: cesiumkit.widget
