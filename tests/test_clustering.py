"""Tests for entity clustering configuration."""

import cesiumkit


class TestEntityClusterConfig:
    def test_default_statements(self):
        statements = cesiumkit.EntityClusterConfig().to_js_statements()
        assert statements == [
            "viewer.entities.clustering.enabled = true;",
            "viewer.entities.clustering.pixelRange = 80;",
            "viewer.entities.clustering.minimumClusterSize = 2;",
            "viewer.entities.clustering.clusterBillboards = true;",
            "viewer.entities.clustering.clusterLabels = true;",
            "viewer.entities.clustering.clusterPoints = true;",
        ]

    def test_custom_values(self):
        statements = cesiumkit.EntityClusterConfig(
            pixel_range=120,
            minimum_cluster_size=5,
            cluster_points=False,
        ).to_js_statements()
        assert "viewer.entities.clustering.pixelRange = 120;" in statements
        assert "viewer.entities.clustering.minimumClusterSize = 5;" in statements
        assert "viewer.entities.clustering.clusterPoints = false;" in statements

    def test_validation(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            cesiumkit.EntityClusterConfig(pixel_range=0)

    def test_viewer_emits_clustering(self):
        v = cesiumkit.Viewer(clustering=cesiumkit.EntityClusterConfig(pixel_range=100))
        html = v.to_html()
        assert "viewer.entities.clustering.enabled = true;" in html
        assert "viewer.entities.clustering.pixelRange = 100;" in html

    def test_viewer_without_clustering_emits_nothing(self):
        html = cesiumkit.Viewer().to_html()
        assert "entities.clustering" not in html
