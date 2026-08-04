# Enums

Enumeration types that serialize to CesiumJS constants. Use these wherever
the API asks for a mode, event type, or vertical origin.

```python
import cesiumkit

viewer = cesiumkit.Viewer(scene_mode=cesiumkit.SceneMode.SCENE2D)
viewer.add_entity(
    cesiumkit.Entity(
        name="Site",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 0),
        label=cesiumkit.LabelGraphics(
            text="Site",
            vertical_origin=cesiumkit.VerticalOrigin.BOTTOM,
        ),
    )
)
```

::: cesiumkit.enums
