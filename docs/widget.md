# How to render a viewer in a Jupyter notebook

_How-to. Target: a live globe inside a notebook cell, with buttons to
control the clock and receive click events._

The widget runs CesiumJS in the notebook from the CDN — notebooks have no
local server — and mirrors the runtime control API of `show()`. There is no
HTTP server to start or stop.

!!! tip "Prefer a plain browser window?"
    The same control API works over `show()`'s local server — see
    [How to control a live viewer](runtime-control.md).

## 1. Install the widget extra

```bash
pip install "cesiumkit[widget]"
```

## 2. Build a viewer and turn it into a widget

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_entity(
    cesiumkit.Entity(
        name="NYC",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
    )
)

widget = viewer.to_widget()
widget  # display this cell to render the globe
```

## 3. Drive the clock and read it back

```python
widget.set_time("2026-07-14T18:00:00Z")
widget.set_multiplier(60)  # seconds of simulation per real second
widget.animate(True)

current = widget.get_current_time()  # reads the live clock from the browser
```

## 4. React to clicks and save screenshots

```python
widget.on_click(lambda entity_id: print("clicked", entity_id))
widget.screenshot("globe.png")
```

## API reference

- ::: cesiumkit.widget
