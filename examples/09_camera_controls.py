"""Camera controls: Demonstrate fly_to, set_view, and look_at."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Camera Controls",
    animation=False,
    timeline=False,
)

# Add some landmarks to look at
landmarks = [
    ("Statue of Liberty", -74.0445, 40.6892, cesiumkit.Color.GREEN),
    ("Eiffel Tower", 2.2945, 48.8584, cesiumkit.Color.GOLD),
    ("Sydney Opera House", 151.2153, -33.8568, cesiumkit.Color.WHITE),
]

for name, lon, lat, color in landmarks:
    viewer.add_entity(
        cesiumkit.Entity(
            name=name,
            position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
            point=cesiumkit.PointGraphics(
                pixel_size=12,
                color=color,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=2,
                height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
            ),
            label=cesiumkit.LabelGraphics(
                text=name,
                font="14px sans-serif",
                fill_color=color,
                pixel_offset=cesiumkit.Cartesian2(x=0, y=-18),
                height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
            ),
        )
    )

# Set up camera: fly to Statue of Liberty with a nice angle
viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-74.0445, 40.6892, 1000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0.3, pitch=-0.4, roll=0),
    duration=3.0,
)

# You can also use look_at for a fixed viewpoint
# viewer.look_at(
#     cesiumkit.Cartesian3.from_degrees(-74.0445, 40.6892, 0),
#     cesiumkit.HeadingPitchRange(heading=0, pitch=-0.4, range=1000),
# )

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
