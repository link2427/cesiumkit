# CZML Export

Build a CZML document from entities and save or serialize it for any
CesiumJS application.

```python
import cesiumkit

doc = cesiumkit.CzmlDocument()
doc.add_entity(
    cesiumkit.Entity(
        name="Marker",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 100),
        point=cesiumkit.PointGraphics(pixel_size=8, color=cesiumkit.Color.RED),
    )
)
doc.save("output.czml")
```

::: cesiumkit.czml
