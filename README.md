# cesiumkit

**Build CesiumJS 3D globe visualizations entirely in Python.**

[![Docs](https://img.shields.io/badge/docs-link2427.github.io%2Fcesiumkit-blue)](https://link2427.github.io/cesiumkit)
[![Coverage](https://link2427.github.io/cesiumkit/coverage.svg)](https://link2427.github.io/cesiumkit)
[![PyPI version](https://img.shields.io/pypi/v/cesiumkit.svg)](https://pypi.org/project/cesiumkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

cesiumkit gives you a Pythonic, object-oriented API for [CesiumJS](https://cesium.com/cesiumjs/) -- the leading open-source JavaScript library for 3D globes and maps. Define entities, materials, camera views, terrain, imagery, and time-dynamic animations in pure Python, then render them in the browser with a single call.

![Globe hero](https://link2427.github.io/cesiumkit/images/gallery/01_globe_hero.png)

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

<p align="center">
  <em>That's it -- 6 lines from Python to a 3D globe in the browser.</em>
</p>

## Gallery

| | | |
|---|---|---|
| [![Shapes](https://link2427.github.io/cesiumkit/images/gallery/02_shapes.png)](https://link2427.github.io/cesiumkit/gallery/) | [![Cities](https://link2427.github.io/cesiumkit/images/gallery/03_cities.png)](https://link2427.github.io/cesiumkit/gallery/) | [![Flight path](https://link2427.github.io/cesiumkit/images/gallery/04_flight_path.png)](https://link2427.github.io/cesiumkit/gallery/) |
| [![GeoPandas](https://link2427.github.io/cesiumkit/images/gallery/05_geopandas.png)](https://link2427.github.io/cesiumkit/gallery/) | [![Extruded polygons](https://link2427.github.io/cesiumkit/images/gallery/06_polygon_3d.png)](https://link2427.github.io/cesiumkit/gallery/) | [More →](https://link2427.github.io/cesiumkit/gallery/) |

---

## Install

```bash
pip install cesiumkit
```

Requires Python 3.10+. No external binary dependencies.

For GeoPandas / Shapely support:

```bash
pip install cesiumkit[gis]
```

## Features

### GeoPandas / Shapely integration

Drop a `GeoDataFrame` onto the globe in one call. Auto-reprojects to WGS84,
handles mixed geometry types, supports per-feature styling from columns.

```python
import geopandas as gpd
import cesiumkit

gdf = gpd.read_file("countries.geojson")
viewer = cesiumkit.Viewer()
viewer.add_geodataframe(
    gdf,
    name_column="NAME",
    color_column="color_hex",
    extruded_height_column="gdp",   # polygons become 3D prisms
    fill_alpha=0.5,
)
viewer.show()
```

Shapely geometries are also auto-converted anywhere cesiumkit expects
positions — pass a `shapely.Point` directly to `Entity(position=...)` or a
`shapely.Polygon` to `PolygonGraphics(hierarchy=...)`.

### Entities with rich graphics

Points, billboards, labels, polygons, polylines, boxes, cylinders, ellipses, ellipsoids, corridors, walls, rectangles, paths, polyline volumes, and 3D models -- all as clean Python objects.

```python
viewer.add_entity(cesiumkit.Entity(
    name="Headquarters",
    position=cesiumkit.Cartesian3.from_degrees(-77.0369, 38.9072, 0),
    polygon=cesiumkit.PolygonGraphics(
        hierarchy=[
            cesiumkit.Cartesian3.from_degrees(-77.04, 38.91),
            cesiumkit.Cartesian3.from_degrees(-77.03, 38.91),
            cesiumkit.Cartesian3.from_degrees(-77.035, 38.905),
        ],
        material=cesiumkit.Color.CORNFLOWERBLUE.with_alpha(0.6),
        extruded_height=200,
    ),
))
```

### Materials

Solid colors, images, grids, stripes, checkerboards, and polyline-specific materials (glow, arrow, dash, outline).

```python
cesiumkit.StripeMaterial(
    orientation=cesiumkit.StripeOrientation.HORIZONTAL,
    even_color=cesiumkit.Color.WHITE,
    odd_color=cesiumkit.Color.BLUE,
    repeat=5,
)
```

### Time-dynamic animation

Animate entities along paths using sampled position properties with configurable interpolation.

```python
prop = cesiumkit.SampledPositionProperty(interpolation_degree=2)
prop.add_sample(cesiumkit.JulianDate.from_iso8601("2024-01-01T00:00:00Z"),
                cesiumkit.Cartesian3.from_degrees(-122.4, 37.8, 10000))
prop.add_sample(cesiumkit.JulianDate.from_iso8601("2024-01-01T01:00:00Z"),
                cesiumkit.Cartesian3.from_degrees(-73.9, 40.7, 10000))
entity = cesiumkit.Entity(name="Flight", position=prop,
                          path=cesiumkit.PathGraphics(width=2, material=cesiumkit.Color.YELLOW))
```

### Data sources

Load GeoJSON, CZML, and KML directly.

```python
viewer.add_data_source(cesiumkit.GeoJsonDataSource(
    url="https://example.com/data.geojson",
    stroke=cesiumkit.Color.RED,
    fill=cesiumkit.Color.RED.with_alpha(0.3),
))
```

### Camera control

Fly to locations, set fixed viewpoints, or lock the camera to a target.

```python
viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(2.2945, 48.8584, 1000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0.3, pitch=-0.4, roll=0),
    duration=3.0,
)
```

### CZML export

Build visualizations in Python and export to CZML for use in any CesiumJS application.

```python
czml_string = viewer.to_czml_string(indent=2)
viewer.save_czml("output.czml")
```

### Imagery and terrain providers

8 imagery providers (Bing, OpenStreetMap, Mapbox, WMTS, WMS, URL template, Ion, TileMapService) and 3 terrain providers (Cesium Ion world terrain, Cesium Ion asset, ellipsoid).

### Cesium Ion integration

```python
cesiumkit.Ion.set_default_token("your-token-here")
viewer.add_tileset(ion_asset_id=75343)  # e.g., NYC 3D buildings
```

### Interactive events

Add click handlers and custom JavaScript for full interactivity.

```python
viewer.on(
    cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
    cesiumkit.JsCode("""function(click) {
        var picked = viewer.scene.pick(click.position);
        if (Cesium.defined(picked)) viewer.selectedEntity = picked.id;
    }"""),
)
```

---

## Full feature list

- **16 entity graphics types**: point, billboard, label, polygon, polyline, box, cylinder, ellipse, ellipsoid, model, corridor, wall, rectangle, path, polyline volume, tileset
- **9 material types**: solid color, image, grid, stripe, checkerboard, polyline glow/arrow/dash/outline
- **148 named colors** with `.with_alpha()` support
- **Time-dynamic properties**: SampledPositionProperty, SampledProperty, ConstantProperty, TimeIntervalCollectionProperty, ReferenceProperty, CompositeProperty
- **Data sources**: GeoJSON, CZML, KML, custom
- **Imagery providers**: Bing, OSM, Mapbox, WMTS, WMS, URL template, Ion, TMS
- **Terrain providers**: Ion world terrain, Ion asset, ellipsoid
- **Camera operations**: fly_to, set_view, look_at
- **CZML export**: to_czml_string(), save_czml(), CzmlDocument
- **Cesium Ion**: token management, 3D Tilesets, terrain
- **Scene/Globe configuration**: fog, lighting, shadows, depth test, atmosphere
- **Event handling**: ScreenSpaceEventHandler with custom JS callbacks
- **Custom JavaScript injection**: add_script() for arbitrary JS
- **Local HTTP server**: `show()` launches a server and opens the browser
- **Works without Ion token**: falls back to bundled NaturalEarthII imagery
- **Pydantic v2 models**: full validation on all inputs

## API overview

| Module | Key classes |
|--------|-------------|
| `cesiumkit.Viewer` | Main entry point -- configure, add entities, show |
| `cesiumkit.Entity` | Container for a named entity with position + graphics |
| `cesiumkit.Cartesian3` | 3D coordinates, with `.from_degrees()` helper |
| `cesiumkit.Color` | 148 named colors + RGBA + `.with_alpha()` |
| `cesiumkit.*Graphics` | PointGraphics, PolygonGraphics, ModelGraphics, ... |
| `cesiumkit.*Material` | StripeMaterial, PolylineGlowMaterial, ... |
| `cesiumkit.*Property` | SampledPositionProperty, ConstantProperty, ... |
| `cesiumkit.*DataSource` | GeoJsonDataSource, CzmlDataSource, KmlDataSource |
| `cesiumkit.CzmlDocument` | Build and export CZML documents |
| `cesiumkit.Ion` | Token management and 3D Tilesets |

## Examples

The [`examples/`](examples/) directory contains 10 runnable scripts:

| # | File | What it shows |
|---|------|---------------|
| 01 | `basic_point.py` | Minimal point on the globe |
| 02 | `multiple_entities.py` | Points, labels, polygons, polylines |
| 03 | `materials.py` | Stripe, grid, glow, dash materials |
| 04 | `imagery_providers.py` | OpenStreetMap, Bing, custom layers |
| 05 | `time_dynamic.py` | Animated flight path with clock |
| 06 | `data_sources.py` | GeoJSON, CZML, KML loading |
| 07 | `3d_models_and_tilesets.py` | glTF models and 3D Tiles |
| 08 | `czml_export.py` | Export entities to CZML format |
| 09 | `camera_controls.py` | fly_to, set_view, look_at |
| 10 | `event_handlers.py` | Click events and custom JS |

Run any example:

```bash
python examples/01_basic_point.py
# Opens in browser -- Ctrl+C to stop the server
```

## Cesium Ion token

Many examples work without a token (using bundled offline imagery). For full functionality (Bing imagery, world terrain, 3D Tilesets), get a free token at [cesium.com/ion](https://cesium.com/ion/) and set it:

```python
cesiumkit.Ion.set_default_token("your-token-here")
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and how to add new entity types.

## License

[MIT](LICENSE)
