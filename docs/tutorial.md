# Tutorial: build a flight tracker

_Tutorial. Target: a viewer that animates an aircraft along a sampled
route, with a ground path, a trailing flight line, and a camera that
follows. You should end up with a reusable pattern for any
time-dynamic entity._

!!! tip "Just want a single globe?"
    See [How to build your first globe](getting-started.md) — the tutorial
    assumes you have a working `Viewer` already.

This tutorial builds one file, `flight_tracker.py`, step by step. Each
section adds one piece; the final script is complete and runnable.

## 1. Create the viewer and its clock

The flight runs between 18:00 and 19:00 UTC. Set the clock to that window
and make it loop so the animation repeats:

Think of the clock as a video player: `start_time` and `stop_time` are the
clip's boundaries, `current_time` is the playhead, and `multiplier` is the
playback speed.

```python
import cesiumkit

viewer = cesiumkit.Viewer(
    title="Flight Tracker",
    should_animate=True,
    clock=cesiumkit.ClockConfig(
        start_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T18:00:00Z"),
        stop_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T19:00:00Z"),
        current_time=cesiumkit.JulianDate.from_iso8601("2026-07-14T18:00:00Z"),
        clock_range=cesiumkit.ClockRange.LOOP_STOP,
        multiplier=60,  # one simulated minute per real second
    ),
)
```

## 2. Define the route as sampled positions

A `SampledPositionProperty` interpolates between waypoints. Add one sample
per leg of the flight; the altitude is in meters:

```python
route = [
    ("18:00", -0.1276, 51.5072, 12000),  # London
    ("18:20", 2.3522, 48.8566, 11500),  # Paris
    ("18:40", 4.8952, 52.3702, 11000),  # Amsterdam
    ("19:00", -0.1276, 51.5072, 12000),  # back to London
]

position = cesiumkit.SampledPositionProperty(interpolation_degree=2)
for time_str, lon, lat, alt in route:
    position.add_sample(
        cesiumkit.JulianDate.from_iso8601(f"2026-07-14T{time_str}:00Z"),
        cesiumkit.Cartesian3.from_degrees(lon, lat, alt),
    )
```

## 3. Add the aircraft entity

The aircraft is a point with a label and a glowing trail. The `path`
graphics draw the last 30 minutes of travel behind the aircraft:

```python
viewer.add_entity(
    cesiumkit.Entity(
        id="aircraft-1",
        name="Flight A1",
        position=position,
        point=cesiumkit.PointGraphics(
            pixel_size=10,
            color=cesiumkit.Color.WHITE,
            outline_color=cesiumkit.Color.GOLD,
            outline_width=2,
        ),
        label=cesiumkit.LabelGraphics(
            text="A1",
            font="12px monospace",
            fill_color=cesiumkit.Color.GOLD,
            horizontal_origin=cesiumkit.HorizontalOrigin.LEFT,
            pixel_offset=cesiumkit.Cartesian2(x=12, y=0),
        ),
        path=cesiumkit.PathGraphics(
            width=3,
            lead_time=0,
            trail_time=1800,  # 30-minute trail, in seconds
            material=cesiumkit.PolylineGlowMaterial(
                color=cesiumkit.Color.GOLD,
                glow_power=0.15,
            ),
        ),
    )
)
```

## 4. Draw the route on the ground

A second entity traces the full route as a polyline at low altitude, so you
can see the planned path while the aircraft moves:

```python
ground_route = [cesiumkit.Cartesian3.from_degrees(lon, lat, 500) for _, lon, lat, _ in route]
viewer.add_entity(
    cesiumkit.Entity(
        name="Route",
        polyline=cesiumkit.PolylineGraphics(
            positions=ground_route,
            width=2,
            material=cesiumkit.Color.WHITE.with_alpha(0.6),
        ),
    )
)
```

## 5. Run it

```python
viewer.show()  # Ctrl+C to stop the server
```

Save the file and run it:

```bash
python flight_tracker.py
```

You should see the aircraft fly the triangle route with a gold trail, the
white route line on the ground, and the clock looping. To make the camera
follow the aircraft, add

```python
viewer.camera.fly_to_entities()
```

before `show()` and re-run.

## What you built

- A `ClockConfig` window with `LOOP_STOP` and a speed multiplier
- A `SampledPositionProperty` interpolating a route
- Entity `path` graphics for a trailing line
- A polyline for the planned route

The same pattern handles any moving object — vehicles, ships, satellites —
by swapping the waypoints and clock window.
