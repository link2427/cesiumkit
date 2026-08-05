"""Tests for 3D Tiles clipping and model/globe clipping planes."""

import pytest
from pydantic import ValidationError

import cesiumkit


class TestClippingPlane:
    def test_to_js(self):
        plane = cesiumkit.ClippingPlane(
            position=cesiumkit.Cartesian3(x=0, y=0, z=0),
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
        )
        assert plane.to_js() == (
            "new Cesium.ClippingPlane(new Cesium.Cartesian3(0.0, 0.0, 0.0), new Cesium.Cartesian3(0.0, 0.0, 1.0))"
        )

    def test_from_degrees_position(self):
        plane = cesiumkit.ClippingPlane(
            position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7),
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
        )
        assert "Cesium.Cartesian3.fromDegrees(-74.0, 40.7)" in plane.to_js()

    def test_position_and_normal_required(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClippingPlane(position=cesiumkit.Cartesian3(x=0, y=0, z=0))


class TestClippingPlaneCollection:
    def _collection(self, **kwargs):
        return cesiumkit.ClippingPlaneCollection(
            planes=[
                cesiumkit.ClippingPlane(
                    position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7, height=0),
                    normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                )
            ],
            **kwargs,
        )

    def test_to_js_defaults_implicit(self):
        js = self._collection().to_js()
        assert js.startswith("new Cesium.ClippingPlaneCollection({planes: [")
        assert "enabled" not in js
        assert "union" not in js

    def test_to_js_disabled(self):
        assert "enabled: false" in self._collection(enabled=False).to_js()

    def test_to_js_union(self):
        assert "union: true" in self._collection(union=True).to_js()

    def test_empty_planes_rejected(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClippingPlaneCollection(planes=[])


class TestClippingWiring:
    def test_tileset_clipping_planes(self):
        tileset = cesiumkit.Cesium3DTileset(
            url="https://example.com/tileset.json",
            clipping_planes=cesiumkit.ClippingPlaneCollection(
                planes=[
                    cesiumkit.ClippingPlane(
                        position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7),
                        normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                    )
                ]
            ),
        )
        js = tileset.to_js()
        assert "clippingPlanes: new Cesium.ClippingPlaneCollection({" in js
        assert "Cesium.Cartesian3.fromDegrees(-74.0, 40.7)" in js

    def test_tileset_without_clipping_unchanged(self):
        js = cesiumkit.Cesium3DTileset(url="https://example.com/tileset.json").to_js()
        assert "clippingPlanes" not in js

    def test_model_graphics_clipping_planes(self):
        entity = cesiumkit.Entity(
            name="Clipped model",
            model=cesiumkit.ModelGraphics(
                uri="https://example.com/model.glb",
                clipping_planes=cesiumkit.ClippingPlaneCollection(
                    planes=[
                        cesiumkit.ClippingPlane(
                            position=cesiumkit.Cartesian3(x=0, y=0, z=0),
                            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                        )
                    ]
                ),
            ),
        )
        js = entity.to_js()
        assert "clippingPlanes: new Cesium.ClippingPlaneCollection({" in js

    def test_globe_clipping_planes(self):
        viewer = cesiumkit.Viewer(
            globe=cesiumkit.GlobeConfig(
                clipping_planes=cesiumkit.ClippingPlaneCollection(
                    planes=[
                        cesiumkit.ClippingPlane(
                            position=cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7, height=0),
                            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                        )
                    ]
                )
            )
        )
        html = viewer.to_html()
        assert "scene.globe.clippingPlanes = new Cesium.ClippingPlaneCollection({" in html
