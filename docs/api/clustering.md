# Clustering

Cluster nearby points, billboards, and labels into a single badge.

```python
import cesiumkit

viewer = cesiumkit.Viewer(
    clustering=cesiumkit.EntityClusterConfig(
        enabled=True,
        pixel_range=64,
        minimum_cluster_size=2,
    )
)
```

::: cesiumkit.clustering
