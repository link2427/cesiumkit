"""Gallery: GeoPandas integration showcase.

This is the marquee image for the new v0.2.0 feature — one-line loading of a
GeoDataFrame directly onto the globe. Uses an inline synthetic dataset so the
gallery build has no network dependency.
"""

import geopandas as gpd
from shapely.geometry import Point, Polygon

import cesiumkit

GALLERY_TITLE = "GeoPandas Integration"

# Synthetic "cities + regions" dataset — no network calls, deterministic.
gdf = gpd.GeoDataFrame(
    {
        "name": ["HQ", "Warehouse", "Office", "Region A", "Region B"],
        "category": ["point", "point", "point", "polygon", "polygon"],
        "color": ["#ff3366", "#33ffaa", "#3388ff", "#ffaa00", "#aa66ff"],
        "elevation": [0, 0, 0, 200_000, 400_000],
        "geometry": [
            Point(-74.006, 40.7128),
            Point(-73.935, 40.730),
            Point(-73.970, 40.750),
            Polygon(
                [
                    (-74.05, 40.68),
                    (-73.95, 40.68),
                    (-73.95, 40.78),
                    (-74.05, 40.78),
                ]
            ),
            Polygon(
                [
                    (-73.93, 40.68),
                    (-73.85, 40.68),
                    (-73.85, 40.78),
                    (-73.93, 40.78),
                ]
            ),
        ],
    },
    crs="EPSG:4326",
)

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

# The one-line GeoPandas → globe call that's the headline feature of v0.2.0
viewer.add_geodataframe(
    gdf,
    name_column="name",
    color_column="color",
    fill_alpha=0.5,
    stroke=cesiumkit.Color.WHITE,
    stroke_width=2,
    extruded_height_column="elevation",
)

# Focus on Manhattan-ish
viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(-73.97, 40.73, 100_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-0.9, roll=0),
)
