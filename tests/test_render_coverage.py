"""Headless render coverage: every entity graphics type must initialize.

Each case builds a viewer with one entity of the given graphics type and
renders it in Chromium against the bundled Cesium build. A page error
(a JS exception) fails the test; failed *resource* loads (models, tilesets
from the web) are expected offline and do not count.
"""

import pytest

import cesiumkit
from cesiumkit import _vendor

pytestmark = pytest.mark.skipif(_vendor.vendor_dir() is None, reason="bundled Cesium build not present")
pytest.importorskip("playwright")

_PNG_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _pos(lon, lat, height=0):
    return cesiumkit.Cartesian3FromDegrees(longitude=lon, latitude=lat, height=height)


def _entity(key, graphics):
    return cesiumkit.Entity(name=type(graphics).__name__, position=_pos(-74.0, 40.7, 100), **{key: graphics})


GRAPHICS_CASES = [
    ("billboard", "billboard", cesiumkit.BillboardGraphics(image=_PNG_DATA_URI, scale=2.0)),
    ("box", "box", cesiumkit.BoxGraphics(dimensions=cesiumkit.Cartesian3(x=500000, y=500000, z=500000))),
    ("corridor", "corridor", cesiumkit.CorridorGraphics(positions=[_pos(-74.0, 40.7), _pos(-73.9, 40.8)], width=1000)),
    ("cylinder", "cylinder", cesiumkit.CylinderGraphics(length=400000, top_radius=100000, bottom_radius=100000)),
    ("ellipse", "ellipse", cesiumkit.EllipseGraphics(semi_major_axis=300000, semi_minor_axis=200000)),
    ("ellipsoid", "ellipsoid", cesiumkit.EllipsoidGraphics(radii=cesiumkit.Cartesian3(x=200000, y=200000, z=300000))),
    ("label", "label", cesiumkit.LabelGraphics(text="New York", font="24px sans-serif")),
    (
        "model",
        "model",
        cesiumkit.ModelGraphics(uri="https://cesium.com/Samples/models/CesiumAir/Cesium_Air.glb", scale=1.0),
    ),
    ("path", "path", cesiumkit.PathGraphics(lead_time=0, trail_time=60, width=4)),
    (
        "plane",
        "plane",
        cesiumkit.PlaneGraphics(
            plane=cesiumkit.Plane(normal=cesiumkit.Cartesian3(x=0, y=0, z=1), distance=0),
            dimensions=cesiumkit.Cartesian2(x=400000, y=400000),
        ),
    ),
    ("point", "point", cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color(red=1.0, green=0.0, blue=0.0))),
    (
        "polygon",
        "polygon",
        cesiumkit.PolygonGraphics(
            hierarchy=cesiumkit.PolygonHierarchy(
                positions=[_pos(-74.02, 40.70), _pos(-73.98, 40.70), _pos(-74.00, 40.74)]
            )
        ),
    ),
    ("polyline", "polyline", cesiumkit.PolylineGraphics(positions=[_pos(-74.0, 40.7), _pos(-73.9, 40.8)], width=6)),
    (
        "polylineVolume",
        "polyline_volume",
        cesiumkit.PolylineVolumeGraphics(
            positions=[_pos(-74.0, 40.7), _pos(-73.9, 40.8)],
            shape=[
                cesiumkit.Cartesian2(x=-50000, y=-50000),
                cesiumkit.Cartesian2(x=50000, y=-50000),
                cesiumkit.Cartesian2(x=0, y=50000),
            ],
        ),
    ),
    (
        "rectangle",
        "rectangle",
        cesiumkit.RectangleGraphics(
            coordinates=cesiumkit.RectangleCoordsFromDegrees(west=-74.02, south=40.70, east=-73.98, north=40.74)
        ),
    ),
    ("wall", "wall", cesiumkit.WallGraphics(positions=[_pos(-74.0, 40.7, 0), _pos(-73.9, 40.8, 0)])),
    ("tileset", "tileset", cesiumkit.Cesium3DTilesetGraphics(uri="https://example.com/tileset.json")),
]


@pytest.mark.parametrize("case_id,key,graphics", GRAPHICS_CASES, ids=[c[0] for c in GRAPHICS_CASES])
def test_graphics_type_renders(case_id, key, graphics):
    from cesiumkit.testing import render_state

    viewer = cesiumkit.Viewer()
    viewer.add_entity(_entity(key, graphics))
    state = render_state(viewer, wait_ms=5000)
    assert state["pageErrors"] == [], f"{case_id}: {state['pageErrors']}"
    assert state["ok"], f"{case_id}: viewer did not initialize"


def test_all_graphics_types_together():
    """The full set in one viewer: catches cross-type serialization clashes."""
    from cesiumkit.testing import render_state

    viewer = cesiumkit.Viewer()
    for _, key, graphics in GRAPHICS_CASES:
        viewer.add_entity(_entity(key, graphics))
    state = render_state(viewer, wait_ms=8000)
    assert state["pageErrors"] == [], state["pageErrors"]
