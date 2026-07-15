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
