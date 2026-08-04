# Ion

Cesium Ion integration: default token management and Ion-hosted assets.

```python
import cesiumkit

cesiumkit.Ion.set_default_token("your-token-here")

viewer = cesiumkit.Viewer(
    imagery_provider=cesiumkit.IonImageryProvider(asset_id=2),
    terrain_provider=cesiumkit.IonTerrainProvider(asset_id=1),
)
```

::: cesiumkit.ion
