"""CZML export: Build entities in Python and export to CZML format."""

import cesiumkit

viewer = cesiumkit.Viewer(title="CZML Export Demo")

# Add several entities
viewer.add_entity(
    cesiumkit.Entity(
        id="point-philly",
        name="Philadelphia",
        position=cesiumkit.Cartesian3.from_degrees(-75.1652, 39.9526, 0),
        point=cesiumkit.PointGraphics(pixel_size=10, color=cesiumkit.Color.RED),
    )
)

viewer.add_entity(
    cesiumkit.Entity(
        id="point-nyc",
        name="New York City",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 0),
        point=cesiumkit.PointGraphics(pixel_size=10, color=cesiumkit.Color.BLUE),
    )
)

viewer.add_entity(
    cesiumkit.Entity(
        id="line-philly-nyc",
        name="Philly to NYC",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-75.1652, 39.9526),
                cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128),
            ],
            width=3,
            material=cesiumkit.Color.YELLOW,
        ),
    )
)

# Export as CZML
czml_string = viewer.to_czml_string(indent=2)
print("CZML output:")
print(czml_string)

# Save CZML to file
viewer.save_czml("examples/output/08_export.czml")
print("\nSaved CZML to examples/output/08_export.czml")

# You can also use CzmlDocument directly for more control
doc = cesiumkit.CzmlDocument(
    name="Custom CZML",
    clock=cesiumkit.ClockConfig(
        start_time=cesiumkit.JulianDate.from_iso8601("2024-01-01T00:00:00Z"),
        stop_time=cesiumkit.JulianDate.from_iso8601("2024-01-02T00:00:00Z"),
        multiplier=3600,
    ),
)
doc.add_entity(
    cesiumkit.Entity(
        id="custom-entity",
        name="Custom",
        position=cesiumkit.Cartesian3.from_degrees(-100, 40, 0),
    )
)
doc.save("examples/output/08_export_custom.czml")
print("Saved custom CZML to examples/output/08_export_custom.czml")
