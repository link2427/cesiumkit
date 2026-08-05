# How to clip and classify 3D Tiles

_How-to. Goal: hide part of a tileset or model, or paint a polygon onto
terrain. Needs: a tileset URL or Ion asset id, and for classification a
polygon ring of `Cartesian3` points._

## Clip a tileset or model

A `ClippingPlaneCollection` holds one or more `ClippingPlane` objects.
Each plane is defined by a point on the plane and a normal; everything on
the side the normal points away from is clipped away. Attach the
collection to a tileset, a model, or the globe itself.

```python
import cesiumkit

planes = cesiumkit.ClippingPlaneCollection(
    planes=[
        cesiumkit.ClippingPlane(
            position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7, height=0),
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),  # up: keep everything below
        )
    ]
)

# clip a 3D Tiles tileset
tileset = cesiumkit.Cesium3DTileset(
    url="https://example.com/tileset.json",
    clipping_planes=planes,
)
viewer = cesiumkit.Viewer()
viewer.add_data_source(tileset)

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

A normal of `(0, 0, 1)` at a position keeps the hemisphere below that
plane; point the normal the other way to keep the opposite side. With
multiple planes, `union=True` keeps the union of the kept regions
instead of the intersection (the default).

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
)
```

`classification_type` controls what the polygon can paint on:

- `ClassificationType.TERRAIN` — only terrain
- `ClassificationType.CESIUM_3D_TILE` — only 3D Tiles (e.g. buildings)
- `ClassificationType.BOTH` — whichever is underneath (default)

Both features serialize to plain CesiumJS constructor calls, so they work
in `to_html()`, `show()`, and the Jupyter widget identically.

## Reference

- `ClippingPlane`, `ClippingPlaneCollection` — see the [API reference](../api/scene.md)
- `ClassificationPrimitive`, `viewer.add_classification()` — same page
