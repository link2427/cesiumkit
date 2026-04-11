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
# Points sit outside the polygon footprints so they're not hidden inside
# the extruded blocks.
gdf = gpd.GeoDataFrame(
    {
        "name": ["HQ", "Warehouse", "Office", "Region A", "Region B"],
        "category": ["point", "point", "point", "polygon", "polygon"],
        "color": ["#ff3366", "#33ffaa", "#3388ff", "#ffaa00", "#aa66ff"],
        "elevation": [0, 0, 0, 2_000, 4_000],
        "geometry": [
            Point(-74.05, 40.82),
            Point(-73.87, 40.82),
            Point(-73.96, 40.62),
            Polygon(
                [
                    (-74.02, 40.70),
                    (-73.98, 40.70),
                    (-73.98, 40.76),
                    (-74.02, 40.76),
                ]
            ),
            Polygon(
                [
                    (-73.92, 40.70),
                    (-73.88, 40.70),
                    (-73.88, 40.76),
                    (-73.92, 40.76),
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

# Oblique view from south of the cluster so the extruded polygons read
# clearly as 3D blocks and all five features are visible in frame.
viewer.set_view(
    cesiumkit.Cartesian3.from_degrees(-73.95, 40.55, 35_000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-0.85, roll=0),
)
