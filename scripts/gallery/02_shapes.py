"""Gallery: colorful polygons and polylines with different materials."""

import cesiumkit

GALLERY_TITLE = "Shapes & Materials"

viewer = cesiumkit.Viewer(
    title=GALLERY_TITLE,
    imagery_provider=cesiumkit.OpenStreetMapImageryProvider(
        url="https://a.tile.openstreetmap.org/",
    ),
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

# A striped polygon
viewer.add_entity(
    cesiumkit.Entity(
        name="Striped",
        polygon=cesiumkit.PolygonGraphics(
            hierarchy=[
                cesiumkit.Cartesian3.from_degrees(-100, 35),
                cesiumkit.Cartesian3.from_degrees(-95, 35),
                cesiumkit.Cartesian3.from_degrees(-95, 40),
                cesiumkit.Cartesian3.from_degrees(-100, 40),
            ],
            material=cesiumkit.StripeMaterial(
                orientation=cesiumkit.StripeOrientation.HORIZONTAL,
                even_color=cesiumkit.Color.WHITE,
                odd_color=cesiumkit.Color.BLUE.with_alpha(0.7),
                repeat=8,
            ),
        ),
    )
)

# A grid-material polygon
viewer.add_entity(
    cesiumkit.Entity(
        name="Grid",
        polygon=cesiumkit.PolygonGraphics(
            hierarchy=[
                cesiumkit.Cartesian3.from_degrees(-90, 35),
                cesiumkit.Cartesian3.from_degrees(-85, 35),
                cesiumkit.Cartesian3.from_degrees(-85, 40),
                cesiumkit.Cartesian3.from_degrees(-90, 40),
            ],
            material=cesiumkit.GridMaterial(
                color=cesiumkit.Color.LIME.with_alpha(0.6),
                cell_alpha=0.2,
                line_count=cesiumkit.Cartesian2(x=8, y=8),
            ),
        ),
    )
)

# A glowing polyline
viewer.add_entity(
    cesiumkit.Entity(
        name="Glow",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-110, 36, 100_000),
                cesiumkit.Cartesian3.from_degrees(-80, 42, 100_000),
            ],
            width=10,
            material=cesiumkit.PolylineGlowMaterial(color=cesiumkit.Color.HOTPINK, glow_power=0.25),
        ),
    )
)

# Focus camera over the US shapes
viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(-92, 37, 4_000_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-1.3, roll=0),
)
