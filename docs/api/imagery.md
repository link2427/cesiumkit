# Imagery Providers

Base imagery layers for the globe: URL templates, Ion assets, Bing, WMS,
WMTS, single tiles, and more.

```python
import cesiumkit

viewer = cesiumkit.Viewer(
    imagery_provider=cesiumkit.UrlTemplateImageryProvider(
        url="https://tiles.example.com/{z}/{x}/{y}.png",
        maximum_level=18,
    )
)
```

::: cesiumkit.imagery
