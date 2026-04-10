"""Gallery: ~20 labeled world cities shown as clamped points with labels."""

import cesiumkit

GALLERY_TITLE = "World Cities"

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

cities = [
    ("New York", -74.006, 40.7128),
    ("Los Angeles", -118.2437, 34.0522),
    ("Mexico City", -99.1332, 19.4326),
    ("São Paulo", -46.6333, -23.5505),
    ("Buenos Aires", -58.3816, -34.6037),
    ("Lima", -77.0428, -12.0464),
    ("London", -0.1278, 51.5074),
    ("Paris", 2.3522, 48.8566),
    ("Berlin", 13.4050, 52.5200),
    ("Rome", 12.4964, 41.9028),
    ("Moscow", 37.6173, 55.7558),
    ("Istanbul", 28.9784, 41.0082),
    ("Cairo", 31.2357, 30.0444),
    ("Lagos", 3.3792, 6.5244),
    ("Cape Town", 18.4241, -33.9249),
    ("Mumbai", 72.8777, 19.0760),
    ("Beijing", 116.4074, 39.9042),
    ("Tokyo", 139.6917, 35.6895),
    ("Singapore", 103.8198, 1.3521),
    ("Sydney", 151.2093, -33.8688),
]

for name, lon, lat in cities:
    viewer.add_entity(
        cesiumkit.Entity(
            name=name,
            position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
            point=cesiumkit.PointGraphics(
                pixel_size=9,
                color=cesiumkit.Color.GOLD,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=1,
            ),
            label=cesiumkit.LabelGraphics(
                text=name,
                font="12px sans-serif",
                fill_color=cesiumkit.Color.WHITE,
                outline_color=cesiumkit.Color.BLACK,
                outline_width=2,
                style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
                pixel_offset=cesiumkit.Cartesian2(x=0, y=-16),
            ),
        )
    )

viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(20, 20, 22_000_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-1.57, roll=0),
)
