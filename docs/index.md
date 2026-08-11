# cesiumkit

**Build CesiumJS 3D globe visualizations entirely in Python.**

cesiumkit is a Pythonic, object-oriented API for
[CesiumJS](https://cesium.com/cesiumjs/), the open-source JavaScript library
for 3D globes and maps. Define entities, materials, camera views, terrain,
imagery, and time-dynamic animations in pure Python, then render them in the
browser with a single call.

## Why cesiumkit?

The same globe, two ways:

=== "With raw CesiumJS (JavaScript)"

    ```html
    <!DOCTYPE html>
    <html>
    <head>
      <style>html, body, #cesiumContainer { width: 100%; height: 100%; margin: 0; }</style>
    </head>
    <body>
      <div id="cesiumContainer"></div>
      <script src="https://cesium.com/downloads/cesiumjs/releases/1.144/Build/Cesium/Cesium.js"></script>
      <script>
        const viewer = new Cesium.Viewer("cesiumContainer", { baseLayerPicker: false });
        viewer.entities.add({
          name: "New York",
          position: Cesium.Cartesian3.fromDegrees(-74.006, 40.7128, 400),
          point: { pixelSize: 12, color: Cesium.Color.RED }
        });
      </script>
    </body>
    </html>
    ```

    You write HTML, wire up the script tag, and remember Cesium's camelCase
    API from memory.

=== "With cesiumkit (Python)"

    ```python
    import cesiumkit

    viewer = cesiumkit.Viewer(title="Hello Globe")
    viewer.add_entity(
        cesiumkit.Entity(
            name="New York",
            position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
            point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
        )
    )
    viewer.show()  # opens in your browser
    ```

    You write Python, get autocomplete and validation, and `show()` serves
    the page.

## What you get

- **17 entity graphics types**: point, billboard, label, polygon, polyline, box, cylinder, ellipse, ellipsoid, model, corridor, wall, rectangle, path, plane, polyline volume, tileset
- **Particle systems**: scene primitives for smoke, fire, weather, and trails
- **9 material types**: solid color, image, grid, stripe, checkerboard, polyline glow/arrow/dash/outline
- **148 named colors** with `.with_alpha()` support
- **Time-dynamic properties**: SampledPositionProperty, SampledProperty, ConstantProperty, and more
- **Data sources**: load GeoJSON, CZML, and KML directly
- **8 imagery providers**: Bing, OSM, SingleTile, WMTS, WMS, URL template, Ion, TMS
- **Terrain providers**: Ion world terrain, Ion asset, Cesium terrain server, ellipsoid, encoded WMS/WMTS heightmaps
- **Camera operations**: fly_to, set_view, look_at
- **CZML export**: export entities for use in any CesiumJS application
- **Cesium Ion integration**: token management, 3D Tilesets, terrain
- **Scene/Globe configuration**: fog, lighting, depth test, atmosphere
- **Event handling**: click events with custom JavaScript callbacks
- **Pydantic v2 models**: full validation on all inputs
- **Type-checked**: PEP 561 `py.typed` marker ships in the wheel; the public API is pyright-clean
- **No Ion token required for local `show()`**: uses NaturalEarthII imagery

## Quick links

- [Getting Started](getting-started.md): install and first visualization
- [Tutorial](tutorial.md): build a flight tracker step by step
- [Examples](examples/index.md): 12 runnable example scripts
- [API Reference](api/index.md): full auto-generated docs
