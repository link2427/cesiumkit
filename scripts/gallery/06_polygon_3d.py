"""Gallery: extruded 3D polygons (building-footprint style)."""

import random

import cesiumkit

GALLERY_TITLE = "Extruded Polygons"

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

# A grid of extruded "buildings" near a fixed lon/lat
random.seed(7)

center_lon, center_lat = -73.9857, 40.7484  # Empire State area
step = 0.0015
colors = [
    cesiumkit.Color.CORNFLOWERBLUE,
    cesiumkit.Color.HOTPINK,
    cesiumkit.Color.GOLD,
    cesiumkit.Color.LIGHTGREEN,
    cesiumkit.Color.SALMON,
    cesiumkit.Color.ORCHID,
]

for i in range(-3, 4):
    for j in range(-3, 4):
        lon = center_lon + i * step
        lat = center_lat + j * step
        half = step * 0.35
        height = random.randint(80, 320)
        color = random.choice(colors)
        viewer.add_entity(
            cesiumkit.Entity(
                polygon=cesiumkit.PolygonGraphics(
                    hierarchy=[
                        cesiumkit.Cartesian3.from_degrees(lon - half, lat - half),
                        cesiumkit.Cartesian3.from_degrees(lon + half, lat - half),
                        cesiumkit.Cartesian3.from_degrees(lon + half, lat + half),
                        cesiumkit.Cartesian3.from_degrees(lon - half, lat + half),
                    ],
                    material=color.with_alpha(0.85),
                    extruded_height=height,
                    outline=True,
                    outline_color=cesiumkit.Color.BLACK,
                ),
            )
        )

viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(center_lon - 0.005, center_lat - 0.01, 1500),
    orientation=cesiumkit.HeadingPitchRoll(heading=0.5, pitch=-0.5, roll=0),
)
