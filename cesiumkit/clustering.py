"""Entity clustering configuration for CesiumJS EntityCluster."""

from __future__ import annotations

from pydantic import Field

from cesiumkit.base import CesiumBase


class EntityClusterConfig(CesiumBase):
    """Configure clustering of points, billboards, and labels.

    Maps to Cesium's ``EntityCollection.clustering``, which is an
    ``EntityCluster`` instance. Clustering groups nearby entities into a
    single cluster label once they are closer than ``pixel_range``.
    """

    enabled: bool = True
    pixel_range: int = Field(default=80, ge=1)
    minimum_cluster_size: int = Field(default=2, ge=1)
    cluster_billboards: bool = True
    cluster_labels: bool = True
    cluster_points: bool = True

    def _js_class_name(self) -> str:
        return "Cesium.EntityCluster"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Return JS statements configuring the viewer's entity clustering."""
        cluster = f"{viewer_var}.entities.clustering"
        return [
            f"{cluster}.enabled = {str(self.enabled).lower()};",
            f"{cluster}.pixelRange = {self.pixel_range};",
            f"{cluster}.minimumClusterSize = {self.minimum_cluster_size};",
            f"{cluster}.clusterBillboards = {str(self.cluster_billboards).lower()};",
            f"{cluster}.clusterLabels = {str(self.cluster_labels).lower()};",
            f"{cluster}.clusterPoints = {str(self.cluster_points).lower()};",
        ]


__all__ = [
    "EntityClusterConfig",
]
