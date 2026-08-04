# Camera

Camera operations for the default viewer camera: fly, look at a target,
or jump instantly.

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.camera.fly_to(
    cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 250000),
    duration=3.0,
)
viewer.camera.look_at(
    cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 0),
    cesiumkit.HeadingPitchRange(pitch=-0.5),
)
```

::: cesiumkit.camera
