# Clock & Time

Clock configuration for the viewer timeline, plus `JulianDate` for ISO 8601
times in time-dynamic properties.

```python
import cesiumkit

viewer = cesiumkit.Viewer(
    clock=cesiumkit.ClockConfig(
        start_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T18:00:00Z"),
        stop_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T19:00:00Z"),
        current_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T18:30:00Z"),
        multiplier=60,
    ),
    should_animate=True,
)
```

::: cesiumkit.clock
