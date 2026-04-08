"""Multiple cities: Plot several cities as points with billboards and labels."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="World Cities",
    animation=False,
    timeline=False,
    home_button=True,
)

cities = [
    ("New York", -74.006, 40.7128, cesiumkit.Color.RED),
    ("London", -0.1278, 51.5074, cesiumkit.Color.BLUE),
    ("Tokyo", 139.6917, 35.6895, cesiumkit.Color.HOTPINK),
    ("Sydney", 151.2093, -33.8688, cesiumkit.Color.GREEN),
    ("Cairo", 31.2357, 30.0444, cesiumkit.Color.GOLD),
    ("Rio de Janeiro", -43.1729, -22.9068, cesiumkit.Color.ORANGE),
    ("Mumbai", 72.8777, 19.0760, cesiumkit.Color.PURPLE),
    ("Los Angeles", -118.2437, 34.0522, cesiumkit.Color.CYAN),
    ("Moscow", 37.6173, 55.7558, cesiumkit.Color.SALMON),
    ("Cape Town", 18.4241, -33.9249, cesiumkit.Color.LIME),
]

for name, lon, lat, color in cities:
    viewer.add_entity(cesiumkit.Entity(
        name=name,
        description=f"<h2>{name}</h2><p>Lon: {lon}, Lat: {lat}</p>",
        position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
        point=cesiumkit.PointGraphics(
            pixel_size=10,
            color=color,
            outline_color=cesiumkit.Color.WHITE,
            outline_width=2,
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
        label=cesiumkit.LabelGraphics(
            text=name,
            font="14px sans-serif",
            fill_color=cesiumkit.Color.WHITE,
            outline_color=cesiumkit.Color.BLACK,
            outline_width=2,
            style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
            pixel_offset=cesiumkit.Cartesian2(x=0, y=-18),
            distance_display_condition=cesiumkit.DistanceDisplayCondition(near=0, far=8000000),
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
    ))

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
