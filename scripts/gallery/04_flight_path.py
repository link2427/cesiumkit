"""Gallery: a flight arc from New York to Paris with a glowing path."""

import cesiumkit

GALLERY_TITLE = "Flight Path"

viewer = cesiumkit.Viewer(
    title=GALLERY_TITLE,
    animation=False,
    timeline=False,
    base_layer_picker=False,
    fullscreen_button=False,
    geocoder=False,
    home_button=False,
    info_box=False,
    scene_mode_picker=False,
    navigation_help_button=False,
    selection_indicator=False,
)

# A simple arc NYC -> Paris, 8 samples to approximate a great circle visually
arc = [
    (-74.006, 40.7128, 0),
    (-60, 45, 6_000_000),
    (-45, 50, 9_000_000),
    (-30, 53, 10_500_000),
    (-15, 54, 10_500_000),
    (0, 52, 9_000_000),
    (2.3522, 48.8566, 0),
]

viewer.add_entity(
    cesiumkit.Entity(
        name="NYC → Paris",
        polyline=cesiumkit.PolylineGraphics(
            positions=[cesiumkit.Cartesian3.from_degrees(lon, lat, h) for lon, lat, h in arc],
            width=6,
            material=cesiumkit.PolylineGlowMaterial(color=cesiumkit.Color.CYAN, glow_power=0.3),
        ),
    )
)

# Endpoints
for label, (lon, lat, _) in [("NYC", arc[0]), ("Paris", arc[-1])]:
    viewer.add_entity(
        cesiumkit.Entity(
            name=label,
            position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
            point=cesiumkit.PointGraphics(
                pixel_size=12,
                color=cesiumkit.Color.YELLOW,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=2,
            ),
            label=cesiumkit.LabelGraphics(
                text=label,
                font="bold 14px sans-serif",
                fill_color=cesiumkit.Color.WHITE,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=3,
                style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
                pixel_offset=cesiumkit.Cartesian2(x=0, y=-20),
            ),
        )
    )

# Straight-down over the mid-Atlantic keeps NYC and Paris both in frame
# without the globe drifting into a corner.
viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(-35, 50, 13_000_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-1.5707963, roll=0),
)
