# Materials

Fill and line materials for polygons, polylines, and other graphics:
solid color, image, grid, stripe, checkerboard, and the polyline
glow/arrow/dash/outline variants.

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_entity(
    cesiumkit.Entity(
        name="Road",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-74.0, 40.7),
                cesiumkit.Cartesian3.from_degrees(-73.9, 40.8),
            ],
            material=cesiumkit.PolylineArrowMaterial(color=cesiumkit.Color.GOLD),
            width=8,
        ),
    )
)
```

::: cesiumkit.material
