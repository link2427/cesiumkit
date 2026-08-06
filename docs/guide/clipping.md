# How to clip and classify 3D Tiles

_How-to. Goal: hide part of a tileset or model, or paint a polygon onto
terrain. Needs: a tileset URL or Ion asset id, and for classification a
polygon ring of `Cartesian3` points._

## Clip a tileset or model

A `ClippingPlaneCollection` holds one or more `ClippingPlane` objects.
Each plane uses Cesium's Hessian normal form: a normalized Cartesian
`normal` and a signed `distance` from the owning object's coordinate-system
origin. Attach the collection to a tileset, a model, or the globe itself.

```python
import cesiumkit

planes = cesiumkit.ClippingPlaneCollection(
    planes=[
        cesiumkit.ClippingPlane(
            normal=cesiumkit.Cartesian3(x=0, y=1, z=0),
            distance=5.0,
        )
    ]
)

# clip a 3D Tiles tileset
viewer = cesiumkit.Viewer()
viewer.add_tileset(url="https://example.com/tileset.json", clipping_planes=planes)

# clip a glTF model the same way
viewer.add_entity(
    cesiumkit.Entity(
        name="Clipped model",
        model=cesiumkit.ModelGraphics(
            uri="https://example.com/model.glb",
            clipping_planes=planes,
        ),
    )
)

# or clip the whole globe at a plane
viewer = cesiumkit.Viewer(globe=cesiumkit.GlobeConfig(clipping_planes=planes))
```

The example plane is at `y = -5` in the clipped object's local coordinate
system. Its positive normal faces the origin, so Cesium clips the region
behind the plane (`y < -5`). Use
`ClippingPlane.from_point_normal(point, normal)` when you already have a
concrete Cartesian point on the plane; geodetic `from_degrees` positions
cannot be used as normal vectors.

With multiple planes, `union_clipping_regions=True` clips a region when it
is outside any plane. The default clips a region only when it is outside
every plane.

## Classify: draw onto terrain or 3D Tiles

Classification renders a filled polygon by reusing the depth of whatever
is underneath it, so the shape drapes over hills and buildings instead of
floating above them.

```python
import cesiumkit

viewer = cesiumkit.Viewer()

viewer.add_classification(
    [
        cesiumkit.Cartesian3FromDegrees(longitude=-74.02, latitude=40.70),
        cesiumkit.Cartesian3FromDegrees(longitude=-73.98, latitude=40.70),
        cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.74),
    ],
    color=cesiumkit.Color(red=0.0, green=0.6, blue=0.9, alpha=0.6),
    height=0.0,
    extruded_height=100_000.0,
)
```

The two heights bound a closed volume that must enclose the surfaces being
classified. Cesium does not render a surface-following classification polygon
without extrusion; the values above are the defaults.

`classification_type` controls what the polygon can paint on:

- `ClassificationType.TERRAIN` — only terrain
- `ClassificationType.CESIUM_3D_TILE` — only 3D Tiles (e.g. buildings)
- `ClassificationType.BOTH` — whichever is underneath (default)

Both features serialize to plain CesiumJS constructor calls, so they work
in `to_html()`, `show()`, and the Jupyter widget identically.

## Reference

- `ClippingPlane`, `ClippingPlaneCollection` — see the [API reference](../api/scene.md)
- `ClassificationPrimitive`, `viewer.add_classification()` — same page
