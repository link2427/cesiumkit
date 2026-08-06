# How to build your first globe

_How-to. Target: a local `show()` viewer with a point and a polygon, running
offline-friendly, in about 20 lines._

!!! tip "Looking for something else?"
    - GeoPandas data on the globe? Skip to [How to plot a GeoDataFrame](getting-started-gis.md).
    - A notebook widget? Skip to [How to use the Jupyter widget](widget.md).
    - Big rasters or point clouds? Skip to [How to display rasters and large point data](raster.md).

## 1. Install

```bash
pip install cesiumkit
```

Requires Python 3.10+. No external binary dependencies. Published wheels
include CesiumJS for local `show()` sessions (see [Offline use](#7-offline-use)).

## 2. Create a viewer and add a point

```python
import cesiumkit

viewer = cesiumkit.Viewer(title="Hello Globe")  # (1)!
viewer.add_entity(
    cesiumkit.Entity(
        name="New York",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),  # (2)!
        point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
    )
)
```

1.  Builds a `Viewer` — nothing is shown yet.
2.  `from_degrees` takes longitude, latitude, and altitude in meters.

## 3. Add a polygon

```python
viewer.add_entity(
    cesiumkit.Entity(
        name="Headquarters",
        position=cesiumkit.Cartesian3.from_degrees(-77.0369, 38.9072, 0),
        polygon=cesiumkit.PolygonGraphics(
            hierarchy=[
                cesiumkit.Cartesian3.from_degrees(-77.04, 38.91),
                cesiumkit.Cartesian3.from_degrees(-77.03, 38.91),
                cesiumkit.Cartesian3.from_degrees(-77.035, 38.905),
            ],
            material=cesiumkit.Color.CORNFLOWERBLUE.with_alpha(0.6),
            extruded_height=200,  # (1)!
        ),
    )
)
```

1.  `extruded_height` lifts the polygon off the ground, making it a 3D prism.

## 4. Show it

```python
viewer.show()
```

This opens your default browser with an interactive 3D globe. Press
`Ctrl+C` to stop the local server.

## 5. Add a Cesium Ion token (optional)

With `Viewer.show()`, an installed wheel uses bundled NaturalEarthII imagery
when no token or imagery provider is configured. For Bing imagery, world
terrain, or 3D Tilesets, get a free token at
[cesium.com/ion](https://cesium.com/ion/):

```python
cesiumkit.Ion.set_default_token("your-token-here")
```

## 6. See what's next

- Browse the [Examples](examples/index.md) for common patterns
- Explore the [API Reference](api/viewer.md) for all available classes
- Follow the [Flight tracker tutorial](tutorial.md) to build something
  multi-step

## 7. Offline use

Published wheels already include CesiumJS 1.144. `Viewer.show()` serves that
local build and its NaturalEarthII imagery, so it can run without network
access when the scene does not request remote imagery, terrain, data, or Ion
resources. Source checkouts leave the large vendor directory out of Git; fetch
it before testing an offline local server:

```bash
python scripts/fetch_cesium.py
```

`to_html()`/`save()` and Jupyter embedding always load Cesium from the CDN;
the package does not currently produce an offline standalone static export.
