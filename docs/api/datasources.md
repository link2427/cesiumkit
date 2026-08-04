# Data Sources

Load external data (GeoJSON, CZML, KML), stream 3D Tilesets with per-feature
styles, or build a custom data source in Python.

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_data_source(cesiumkit.GeoJsonDataSource(url="https://example.com/cities.geojson", clamp_to_ground=True))
viewer.add_data_source(
    cesiumkit.Cesium3DTileset(
        url="https://example.com/tileset.json",
        style=cesiumkit.Cesium3DTileStyle(
            color_conditions=[
                ["${height} > 100", "color('red')"],
                ["true", "color('white')"],
            ]
        ),
    )
)

# A custom source you can attach entities to in Python
custom = cesiumkit.CustomDataSource(name="my_sources")
custom.entities.add(
    cesiumkit.Entity(
        name="Custom",
        position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
    )
)
viewer.add_data_source(custom)
```

::: cesiumkit.datasources
