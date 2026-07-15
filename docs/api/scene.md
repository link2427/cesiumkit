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

CesiumJS 1.119 applies these settings through the scene's vertical
exaggeration properties; `GlobeConfig` provides the Python-facing grouping.

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
