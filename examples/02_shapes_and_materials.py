"""Shapes and materials: polygons, polylines, boxes, cylinders with various materials."""

import cesiumkit

viewer = cesiumkit.Viewer(
    title="Shapes & Materials",
    animation=False,
    timeline=False,
)

# --- Striped polygon ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Striped Polygon",
        polygon=cesiumkit.PolygonGraphics(
            hierarchy=[
                cesiumkit.Cartesian3.from_degrees(-115, 37),
                cesiumkit.Cartesian3.from_degrees(-115, 32),
                cesiumkit.Cartesian3.from_degrees(-107, 33),
                cesiumkit.Cartesian3.from_degrees(-102, 31),
                cesiumkit.Cartesian3.from_degrees(-102, 35),
            ],
            material=cesiumkit.StripeMaterial(
                even_color=cesiumkit.Color.GREEN.with_alpha(0.5),
                odd_color=cesiumkit.Color.BLUE.with_alpha(0.5),
                repeat=5.0,
            ),
            extruded_height=100000,
            outline=True,
            outline_color=cesiumkit.Color.BLACK,
        ),
    )
)

# --- Glowing polyline ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Glowing Line",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-75, 35, 200000),
                cesiumkit.Cartesian3.from_degrees(-125, 35, 200000),
            ],
            width=10,
            material=cesiumkit.PolylineGlowMaterial(
                color=cesiumkit.Color.CYAN,
                glow_power=0.2,
            ),
        ),
    )
)

# --- Dashed polyline ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Dashed Line",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-75, 40, 200000),
                cesiumkit.Cartesian3.from_degrees(-125, 40, 200000),
            ],
            width=4,
            material=cesiumkit.PolylineDashMaterial(
                color=cesiumkit.Color.YELLOW,
                dash_length=16.0,
            ),
        ),
    )
)

# --- Arrow polyline ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Arrow Line",
        polyline=cesiumkit.PolylineGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-75, 45, 200000),
                cesiumkit.Cartesian3.from_degrees(-125, 45, 200000),
            ],
            width=10,
            material=cesiumkit.PolylineArrowMaterial(
                color=cesiumkit.Color.ORANGE,
            ),
        ),
    )
)

# --- Box ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Blue Box",
        position=cesiumkit.Cartesian3.from_degrees(-90, 40, 200000),
        box=cesiumkit.BoxGraphics(
            dimensions=cesiumkit.Cartesian3(x=400000, y=300000, z=500000),
            material=cesiumkit.Color.CORNFLOWERBLUE.with_alpha(0.7),
            outline=True,
            outline_color=cesiumkit.Color.WHITE,
        ),
    )
)

# --- Cylinder ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Red Cylinder",
        position=cesiumkit.Cartesian3.from_degrees(-80, 40, 200000),
        cylinder=cesiumkit.CylinderGraphics(
            length=400000,
            top_radius=100000,
            bottom_radius=200000,
            material=cesiumkit.Color.RED.with_alpha(0.7),
            outline=True,
            outline_color=cesiumkit.Color.DARKRED,
        ),
    )
)

# --- Ellipsoid (sphere) ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Green Sphere",
        position=cesiumkit.Cartesian3.from_degrees(-70, 40, 200000),
        ellipsoid=cesiumkit.EllipsoidGraphics(
            radii=cesiumkit.Cartesian3(x=200000, y=200000, z=200000),
            material=cesiumkit.Color.LIME.with_alpha(0.6),
            outline=True,
            outline_color=cesiumkit.Color.DARKGREEN,
        ),
    )
)

# --- Ellipse on ground ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Purple Ellipse",
        position=cesiumkit.Cartesian3.from_degrees(-100, 30),
        ellipse=cesiumkit.EllipseGraphics(
            semi_major_axis=300000,
            semi_minor_axis=150000,
            material=cesiumkit.CheckerboardMaterial(
                even_color=cesiumkit.Color.PURPLE.with_alpha(0.5),
                odd_color=cesiumkit.Color.WHITE.with_alpha(0.3),
            ),
            rotation=0.5,
        ),
    )
)

# --- Wall ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Orange Wall",
        wall=cesiumkit.WallGraphics(
            positions=[
                cesiumkit.Cartesian3.from_degrees(-60, 42),
                cesiumkit.Cartesian3.from_degrees(-55, 42),
                cesiumkit.Cartesian3.from_degrees(-55, 38),
                cesiumkit.Cartesian3.from_degrees(-60, 38),
            ],
            maximum_heights=[200000, 200000, 200000, 200000],
            minimum_heights=[0, 0, 0, 0],
            material=cesiumkit.Color.ORANGE.with_alpha(0.6),
        ),
    )
)

# --- Rectangle ---
viewer.add_entity(
    cesiumkit.Entity(
        name="Grid Rectangle",
        rectangle=cesiumkit.RectangleGraphics(
            coordinates=cesiumkit.RectangleCoords.from_degrees(-130, 25, -120, 30),
            material=cesiumkit.GridMaterial(
                color=cesiumkit.Color.YELLOW,
                cell_alpha=0.2,
            ),
        ),
    )
)

viewer.fly_to(
    cesiumkit.Cartesian3.from_degrees(-100, 38, 5000000),
    duration=2.0,
)

viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
