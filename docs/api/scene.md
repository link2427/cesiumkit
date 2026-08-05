# Scene & Globe

Scene and globe configuration options.

## Scene

::: cesiumkit.scene

## Globe

::: cesiumkit.globe

Terrain can be vertically exaggerated relative to a reference height:

```python
globe = cesiumkit.GlobeConfig(
    terrain_exaggeration=3.0,
    terrain_exaggeration_relative_height=100.0,
)
viewer = cesiumkit.Viewer(globe=globe)
```

CesiumJS 1.144 applies these settings through the scene's vertical
exaggeration properties; `GlobeConfig` provides the Python-facing grouping.

## Clipping planes

Tilesets, models, and the globe can be clipped by a set of planes. Each
plane is a point plus a normal; everything on the normal's far side is
cut away. See [How to clip and classify 3D Tiles](../guide/clipping.md).

```python
planes = cesiumkit.ClippingPlaneCollection(
    planes=[
        cesiumkit.ClippingPlane(
            position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7, height=0),
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
        )
    ]
)
tileset = cesiumkit.Cesium3DTileset(url="https://example.com/tileset.json", clipping_planes=planes)
```

`union=True` switches the collection from intersection to union of the
kept regions; `enabled=False` keeps the planes but turns them off.

## Classification

`ClassificationPrimitive` (or the `viewer.add_classification()` helper)
draws a filled polygon that drapes over terrain or 3D Tiles by reusing
their depth:

```python
viewer.add_classification(
    [
        cesiumkit.Cartesian3FromDegrees(longitude=-74.02, latitude=40.70),
        cesiumkit.Cartesian3FromDegrees(longitude=-73.98, latitude=40.70),
        cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.74),
    ],
    color=cesiumkit.Color(red=0.0, green=0.6, blue=0.9, alpha=0.6),
)
```

## Fog, atmosphere, and antialiasing

`SceneConfig` exposes the stable scene-quality knobs that don't change the
viewer's construction:

```python
scene = cesiumkit.SceneConfig(
    fog_density=0.0002,
    fog_minimum_brightness=0.5,
    atmosphere_hue_shift=0.1,
    atmosphere_saturation_shift=-0.05,
    msaa_samples=4,
)
viewer = cesiumkit.Viewer(scene=scene)
```

- `fog_*` maps to `scene.fog` (density, minimum brightness, screen-space
  error factor).
- `atmosphere_*` maps to `scene.skyAtmosphere` (brightness/hue/saturation
  shifts, each in `[-1, 1]`).
- `msaa_samples` sets `scene.msaaSamples` (1-16).

## Rendering performance

Viewer constructor controls expose explicit rendering, resolution scaling,
frame-rate limits, and render-loop error reporting:

```python
viewer = cesiumkit.Viewer(
    request_render_mode=True,
    maximum_render_time_change=0.0,
    resolution_scale=0.75,
    target_frame_rate=30,
    show_renderer_errors=True,
)
```

`SceneConfig` also exposes `request_render_mode` and
`maximum_render_time_change` for post-construction scene configuration.

## Post-processing

Bloom, FXAA, and ambient occlusion are independently configurable. No stages
are changed unless a config is explicitly supplied:

```python
scene = cesiumkit.SceneConfig(
    post_process=cesiumkit.PostProcessConfig(
        bloom=cesiumkit.BloomConfig(enabled=True, contrast=128, brightness=-0.3),
        fxaa=cesiumkit.FXAAConfig(enabled=True),
        ambient_occlusion=cesiumkit.AmbientOcclusionConfig(enabled=True, intensity=1),
    )
)
viewer = cesiumkit.Viewer(scene=scene)
```
