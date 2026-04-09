# Examples

The [`examples/`](https://github.com/link2427/cesiumkit/tree/main/examples) directory contains 10 runnable scripts covering all major features.

Run any example:

```bash
python examples/01_basic_point.py
# Opens in browser — Ctrl+C to stop the server
```

## Example index

| # | Script | What it shows |
|---|--------|---------------|
| 01 | `01_basic_point.py` | Minimal point on the globe |
| 02 | `02_shapes_and_materials.py` | Points, labels, polygons, polylines, materials |
| 03 | `03_multiple_cities.py` | Multiple entities on the globe |
| 04 | `04_time_dynamic_satellite.py` | Animated flight path with clock |
| 05 | `05_geojson_and_datasources.py` | GeoJSON, CZML, KML loading |
| 06 | `06_terrain_and_imagery.py` | Terrain and imagery providers |
| 07 | `07_3d_models_and_tilesets.py` | glTF models and 3D Tiles |
| 08 | `08_czml_export.py` | Export entities to CZML format |
| 09 | `09_camera_controls.py` | fly_to, set_view, look_at |
| 10 | `10_event_handlers.py` | Click events and custom JavaScript |

## Materials

```python
cesiumkit.StripeMaterial(
    orientation=cesiumkit.StripeOrientation.HORIZONTAL,
    even_color=cesiumkit.Color.WHITE,
    odd_color=cesiumkit.Color.BLUE,
    repeat=5,
)
```

## Time-dynamic animation

```python
prop = cesiumkit.SampledPositionProperty(interpolation_degree=2)
prop.add_sample(
    cesiumkit.JulianDate.from_iso8601("2024-01-01T00:00:00Z"),
    cesiumkit.Cartesian3.from_degrees(-122.4, 37.8, 10000),
)
prop.add_sample(
    cesiumkit.JulianDate.from_iso8601("2024-01-01T01:00:00Z"),
    cesiumkit.Cartesian3.from_degrees(-73.9, 40.7, 10000),
)
entity = cesiumkit.Entity(
    name="Flight",
    position=prop,
    path=cesiumkit.PathGraphics(width=2, material=cesiumkit.Color.YELLOW),
)
```

## Data sources

```python
viewer.add_data_source(cesiumkit.GeoJsonDataSource(
    url="https://example.com/data.geojson",
    stroke=cesiumkit.Color.RED,
    fill=cesiumkit.Color.RED.with_alpha(0.3),
))
```

## Camera control

```python
viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(2.2945, 48.8584, 1000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0.3, pitch=-0.4, roll=0),
    duration=3.0,
)
```

## CZML export

```python
czml_string = viewer.to_czml_string(indent=2)
viewer.save_czml("output.czml")
```

## Interactive events

```python
viewer.on(
    cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
    cesiumkit.JsCode("""function(click) {
        var picked = viewer.scene.pick(click.position);
        if (Cesium.defined(picked)) viewer.selectedEntity = picked.id;
    }"""),
)
```
