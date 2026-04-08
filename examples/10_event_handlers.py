"""Event handlers: Add click interactivity with custom JavaScript."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Click Events",
    animation=False,
    timeline=False,
)

# Add some clickable entities
cities = [
    ("New York", -74.006, 40.7128),
    ("Chicago", -87.6298, 41.8781),
    ("Los Angeles", -118.2437, 34.0522),
    ("Houston", -95.3698, 29.7604),
    ("Phoenix", -112.074, 33.4484),
]

for name, lon, lat in cities:
    viewer.add_entity(
        cesiumkit.Entity(
            name=name,
            description=f"<h2>{name}</h2><p>Click detected!</p>",
            position=cesiumkit.Cartesian3.from_degrees(lon, lat, 0),
            point=cesiumkit.PointGraphics(
                pixel_size=14,
                color=cesiumkit.Color.DODGERBLUE,
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
                pixel_offset=cesiumkit.Cartesian2(x=0, y=-20),
                height_reference=cesiumkit.HeightReference.CLAMP_TO_GROUND,
            ),
        )
    )

# Add a click handler that logs picked entities
viewer.on(
    cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
    cesiumkit.JsCode("""function(click) {
        var pickedObject = viewer.scene.pick(click.position);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
            console.log('Clicked:', pickedObject.id.name);
            viewer.selectedEntity = pickedObject.id;
        }
    }"""),
)

# You can also add arbitrary custom JavaScript
viewer.add_script("""
    // Change cursor on hover
    var handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction(function(movement) {
        var pickedObject = viewer.scene.pick(movement.endPosition);
        viewer.scene.canvas.style.cursor = Cesium.defined(pickedObject) ? 'pointer' : 'default';
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
""")

viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-98, 38, 5000000),
    duration=2.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
