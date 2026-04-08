"""3D models and tilesets: Load glTF models and Cesium 3D Tiles."""

import cesiumkit

# cesiumkit.Ion.set_default_token("YOUR_TOKEN_HERE")

viewer = cesiumkit.Viewer(
    title="3D Models & Tilesets",
)

# Load a glTF model (Cesium's sample milk truck)
viewer.add_entity(
    cesiumkit.Entity(
        name="Milk Truck",
        position=cesiumkit.Cartesian3.from_degrees(-75.59777, 40.03883, 0),
        model=cesiumkit.ModelGraphics(
            uri="https://raw.githubusercontent.com/CesiumGS/cesium/main/Apps/SampleData/models/CesiumMilkTruck/CesiumMilkTruck.glb",
            minimum_pixel_size=64,
            maximum_scale=20000,
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
        label=cesiumkit.LabelGraphics(
            text="Milk Truck",
            font="14px sans-serif",
            fill_color=cesiumkit.Color.WHITE,
            pixel_offset=cesiumkit.Cartesian2(x=0, y=-30),
            height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
        ),
    )
)

# Load a 3D Tileset from Cesium Ion (e.g., New York City buildings)
# Uncomment if you have an Ion token:
# viewer.add_tileset(ion_asset_id=75343)

viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-75.59777, 40.03883, 500),
    orientation=cesiumkit.HeadingPitchRoll(heading=0, pitch=-0.3, roll=0),
    duration=2.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
