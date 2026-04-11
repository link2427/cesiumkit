"""Gallery hero image — a dramatic globe view with several labeled cities.

Gallery scripts follow a convention: build a module-level ``viewer`` and a
module-level ``GALLERY_TITLE``. The orchestrator imports the module, grabs
both, renders HTML to a temp file, and screenshots it with playwright.
"""

import cesiumkit

GALLERY_TITLE = "Globe Hero"

viewer = cesiumkit.Viewer(
    title=GALLERY_TITLE,
    animation=False,
    timeline=False,
    base_layer_picker=False,
    fullscreen_button=False,
    vr_button=False,
    geocoder=False,
    home_button=False,
    info_box=False,
    scene_mode_picker=False,
    selection_indicator=False,
    navigation_help_button=False,
)

cities = [
    ("New York", -74.006, 40.7128, cesiumkit.Color.CYAN),
    ("London", -0.1278, 51.5074, cesiumkit.Color.GOLD),
    ("Tokyo", 139.6917, 35.6895, cesiumkit.Color.HOTPINK),
    ("Sydney", 151.2093, -33.8688, cesiumkit.Color.LIME),
    ("São Paulo", -46.6333, -23.5505, cesiumkit.Color.ORANGE),
    ("Cape Town", 18.4241, -33.9249, cesiumkit.Color.RED),
]

for name, lon, lat, color in cities:
    viewer.add_entity(
        cesiumkit.Entity(
            name=name,
            position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
            point=cesiumkit.PointGraphics(
                pixel_size=14,
                color=color,
                outline_color=cesiumkit.Color.WHITE,
                outline_width=2,
            ),
            label=cesiumkit.LabelGraphics(
                text=name,
                font="bold 16px sans-serif",
                fill_color=cesiumkit.Color.WHITE,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=3,
                style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
                pixel_offset=cesiumkit.Cartesian2(x=0, y=-22),
            ),
        )
    )

# Straight-down view centered over the Atlantic so NYC, London, São Paulo,
# and Cape Town are all visible in the same frame. Pitch=-π/2 keeps the
# globe centered instead of drifting into a corner.
viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(-20, 10, 14_000_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-1.5707963, roll=0),
)
