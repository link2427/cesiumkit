"""Time-dynamic satellite: Animate an entity along a sampled path."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Satellite Tracker",
    should_animate=True,
    clock=cesiumkit.ClockConfig(
        start_time=cesiumkit.JulianDate.from_iso8601("2024-03-15T00:00:00Z"),
        stop_time=cesiumkit.JulianDate.from_iso8601("2024-03-15T06:00:00Z"),
        current_time=cesiumkit.JulianDate.from_iso8601("2024-03-15T00:00:00Z"),
        clock_range=cesiumkit.ClockRange.LOOP_STOP,
        multiplier=60,  # 60x real-time
    ),
)

# Build a sampled position (a simple orbital-like path)
position = cesiumkit.SampledPositionProperty(interpolation_degree=2)

# Add waypoints along a path
waypoints = [
    ("2024-03-15T00:00:00Z", -122.4194, 37.7749, 400000),   # San Francisco
    ("2024-03-15T00:30:00Z", -104.9903, 39.7392, 400000),   # Denver
    ("2024-03-15T01:00:00Z", -87.6298, 41.8781, 400000),    # Chicago
    ("2024-03-15T01:30:00Z", -74.006, 40.7128, 400000),     # New York
    ("2024-03-15T02:00:00Z", -43.1729, -22.9068, 400000),   # Rio
    ("2024-03-15T02:30:00Z", -3.7038, 40.4168, 400000),     # Madrid
    ("2024-03-15T03:00:00Z", 2.3522, 48.8566, 400000),      # Paris
    ("2024-03-15T03:30:00Z", 12.4964, 41.9028, 400000),     # Rome
    ("2024-03-15T04:00:00Z", 37.6173, 55.7558, 400000),     # Moscow
    ("2024-03-15T04:30:00Z", 72.8777, 19.076, 400000),      # Mumbai
    ("2024-03-15T05:00:00Z", 103.8198, 1.3521, 400000),     # Singapore
    ("2024-03-15T05:30:00Z", 139.6917, 35.6895, 400000),    # Tokyo
    ("2024-03-15T06:00:00Z", -122.4194, 37.7749, 400000),   # Back to SF
]

for time_str, lon, lat, alt in waypoints:
    position.add_sample(time_str, cesiumkit.Cartesian3.from_degrees(lon, lat, alt))

# Satellite entity with path trail
viewer.add_entity(cesiumkit.Entity(
    id="satellite-1",
    name="ISS Tracker (simulated)",
    description="<p>Simulated satellite orbit path</p>",
    position=position,
    point=cesiumkit.PointGraphics(
        pixel_size=10,
        color=cesiumkit.Color.WHITE,
        outline_color=cesiumkit.Color.CYAN,
        outline_width=2,
    ),
    label=cesiumkit.LabelGraphics(
        text="ISS",
        font="12px monospace",
        fill_color=cesiumkit.Color.CYAN,
        pixel_offset=cesiumkit.Cartesian2(x=12, y=0),
        horizontal_origin=cesiumkit.HorizontalOrigin.LEFT,
    ),
    path=cesiumkit.PathGraphics(
        width=2,
        lead_time=0,
        trail_time=7200,  # 2-hour trail
        material=cesiumkit.PolylineGlowMaterial(
            color=cesiumkit.Color.CYAN,
            glow_power=0.1,
        ),
    ),
))

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
