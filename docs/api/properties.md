# Properties

Time-dynamic and constant property types. Attach them to entity graphics to
animate values over time (see the
[time-dynamic example](../examples/index.md)).

```python
import cesiumkit

position = cesiumkit.SampledPositionProperty()
position.add_sample(
    cesiumkit.JulianDate.from_iso8601("2026-07-14T18:00:00Z"),
    cesiumkit.Cartesian3.from_degrees(0, 0, 400000),
)
position.add_sample(
    cesiumkit.JulianDate.from_iso8601("2026-07-14T18:05:00Z"),
    cesiumkit.Cartesian3.from_degrees(10, 10, 400000),
)

viewer = cesiumkit.Viewer()
viewer.add_entity(cesiumkit.Entity(name="Satellite", position=position))
```

::: cesiumkit.properties
