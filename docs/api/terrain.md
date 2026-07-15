# Terrain Providers

Configure terrain for the globe.

::: cesiumkit.terrain

## WMS and WMTS elevation images

CesiumJS has no native WMS/WMTS terrain provider. Cesiumkit adapts encoded
elevation images through `Cesium.CustomHeightmapTerrainProvider`:

```python
terrain = cesiumkit.WmsTerrainProvider(
    url="https://terrain.example.com/wms",
    layers="elevation_rgb",
    encoding="terrain-rgb",  # terrain-rgb, terrarium, or grayscale
    maximum_level=14,
)
viewer = cesiumkit.Viewer(terrain_provider=terrain)
```

For WMTS, provide the KVP endpoint, layer, and tile matrix set with
`WmtsTerrainProvider`.

The source layer must return PNG/WebP tiles whose pixels encode elevation in
the selected format. Browser access also requires CORS permission from the
terrain server. `height_scale` and `height_offset` can adjust decoded values,
especially for grayscale layers.
