"""Basic example: Add a point with a label to the globe."""

import cesiumkit

# Optional: set your Cesium Ion token for terrain/imagery
# cesiumkit.Ion.set_default_token("YOUR_TOKEN_HERE")

viewer = cesiumkit.Viewer(
    title="Basic Point Example",
    animation=False,
    timeline=False,
)

viewer.add_entity(
    cesiumkit.Entity(
        name="Philadelphia",
        description="<p>The City of Brotherly Love</p>",
        position=cesiumkit.Cartesian3.from_degrees(-75.1652, 39.9526, 0),
        point=cesiumkit.PointGraphics(
            pixel_size=12,
            color=cesiumkit.Color.RED,
            outline_color=cesiumkit.Color.WHITE,
            outline_width=2,
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
        label=cesiumkit.LabelGraphics(
            text="Philadelphia",
            font="16px Helvetica",
            style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
            fill_color=cesiumkit.Color.YELLOW,
            outline_color=cesiumkit.Color.BLACK,
            outline_width=2,
            pixel_offset=cesiumkit.Cartesian2(x=0, y=-20),
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
    )
)

# Fly to Philadelphia
viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-75.1652, 39.9526, 50000),
    duration=2.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
