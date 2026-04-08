"""Loading external data: GeoJSON, CZML, and KML data sources."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Data Sources Example",
    animation=False,
    timeline=False,
)

# Load GeoJSON from a URL (US states example from Cesium)
viewer.load_geojson(
    url="https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json",
    stroke=cesiumkit.Color.HOTPINK,
    stroke_width=2,
    fill=cesiumkit.Color.PINK.with_alpha(0.3),
    clamp_to_ground=True,
)

# You can also load inline GeoJSON data
viewer.load_geojson(
    data={
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-104.99, 39.74],
                },
                "properties": {
                    "name": "Denver",
                    "population": 715522,
                },
            },
        ],
    },
    marker_color=cesiumkit.Color.RED,
)

viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-98.5795, 39.8283, 5000000),
    duration=2.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
