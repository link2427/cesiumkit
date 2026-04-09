# cesiumkit

**Build CesiumJS 3D globe visualizations entirely in Python.**

cesiumkit gives you a Pythonic, object-oriented API for [CesiumJS](https://cesium.com/cesiumjs/) — the leading open-source JavaScript library for 3D globes and maps. Define entities, materials, camera views, terrain, imagery, and time-dynamic animations in pure Python, then render them in the browser with a single call.

```python
import cesiumkit

viewer = cesiumkit.Viewer(title="Hello Globe")
viewer.add_entity(cesiumkit.Entity(
    name="New York",
    position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
    point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
))
viewer.show()  # opens in your browser
```

## Features

- **16 entity graphics types** — point, billboard, label, polygon, polyline, box, cylinder, ellipse, ellipsoid, model, corridor, wall, rectangle, path, polyline volume, tileset
- **9 material types** — solid color, image, grid, stripe, checkerboard, polyline glow/arrow/dash/outline
- **148 named colors** with `.with_alpha()` support
- **Time-dynamic properties** — SampledPositionProperty, SampledProperty, ConstantProperty, and more
- **Data sources** — load GeoJSON, CZML, and KML directly
- **8 imagery providers** — Bing, OSM, Mapbox, WMTS, WMS, URL template, Ion, TMS
- **3 terrain providers** — Ion world terrain, Ion asset, ellipsoid
- **Camera operations** — fly_to, set_view, look_at
- **CZML export** — export entities for use in any CesiumJS application
- **Cesium Ion integration** — token management, 3D Tilesets, terrain
- **Scene/Globe configuration** — fog, lighting, shadows, depth test, atmosphere
- **Event handling** — click events with custom JavaScript callbacks
- **Pydantic v2 models** — full validation on all inputs
- **Works without an Ion token** — falls back to bundled offline imagery

## Quick links

- [Getting Started](getting-started.md) — install and first visualization
- [Examples](examples.md) — 10 runnable example scripts
- [API Reference](api/viewer.md) — full auto-generated docs
