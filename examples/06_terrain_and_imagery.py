"""Terrain and imagery providers: Configure globe appearance."""

import cesiumkit

# To use Cesium Ion terrain, you need a token:
# cesiumkit.Ion.set_default_token("YOUR_TOKEN_HERE")

viewer = cesiumkit.Viewer(
    title="Terrain & Imagery",
    # Use Cesium World Terrain with vertex normals for lighting
    terrain_provider=cesiumkit.IonTerrainProvider(
        request_vertex_normals=True,
    ),
    # Enable globe lighting
    globe=cesiumkit.GlobeConfig(
        enable_lighting=True,
        depth_test_against_terrain=True,
    ),
    # Scene config
    scene=cesiumkit.SceneConfig(
        fog_enabled=True,
    ),
)

# Add a marker at the Grand Canyon
viewer.add_entity(cesiumkit.Entity(
    name="Grand Canyon",
    position=cesiumkit.Cartesian3.from_degrees(-112.1129, 36.1069, 2000),
    point=cesiumkit.PointGraphics(
        pixel_size=12,
        color=cesiumkit.Color.RED,
        outline_color=cesiumkit.Color.WHITE,
        outline_width=2,
        height_reference=cesiumkit.HeightReference.RELATIVE_TO_GROUND,
    ),
    label=cesiumkit.LabelGraphics(
        text="Grand Canyon",
        font="16px sans-serif",
        fill_color=cesiumkit.Color.WHITE,
        outline_color=cesiumkit.Color.BLACK,
        outline_width=2,
        style=cesiumkit.LabelStyle.FILL_AND_OUTLINE,
        pixel_offset=cesiumkit.Cartesian2(x=0, y=-20),
        height_reference=cesiumkit.HeightReference.RELATIVE_TO_GROUND,
    ),
))

# Fly to Grand Canyon with a nice angle
viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-112.1129, 36.1069, 15000),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-0.5, roll=0),
    duration=3.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
