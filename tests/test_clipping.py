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


class TestClassificationPrimitive:
    def _positions(self):
        return [
            cesiumkit.Cartesian3FromDegrees(longitude=-74.02, latitude=40.70),
            cesiumkit.Cartesian3FromDegrees(longitude=-73.98, latitude=40.70),
            cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.74),
        ]

    def test_to_js_defaults(self):
        js = cesiumkit.ClassificationPrimitive(positions=self._positions()).to_js()
        assert js.startswith("new Cesium.ClassificationPrimitive({")
        assert "new Cesium.PolygonGeometry.fromPositions({" in js
        assert "Cesium.Cartesian3.fromDegrees(-74.02, 40.7)" in js
        assert "classificationType: Cesium.ClassificationType.BOTH" in js
        assert "Cesium.ColorGeometryInstanceAttribute.fromColor(Cesium.Color.RED)" in js
        assert "show" not in js

    def test_to_js_color_and_type(self):
        js = cesiumkit.ClassificationPrimitive(
            positions=self._positions(),
            color=cesiumkit.Color(red=0.2, green=0.5, blue=1.0),
            classification_type=cesiumkit.ClassificationType.TERRAIN,
            show=False,
        ).to_js()
        assert "fromColor(new Cesium.Color(0.2, 0.5, 1.0, 1.0))" in js
        assert "classificationType: Cesium.ClassificationType.TERRAIN" in js
        assert "show: false" in js

    def test_too_few_positions_rejected(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClassificationPrimitive(
                positions=[
                    cesiumkit.Cartesian3(x=0, y=0, z=0),
                    cesiumkit.Cartesian3(x=1, y=0, z=0),
                ]
            )

    def test_add_classification_through_viewer(self):
        viewer = cesiumkit.Viewer()
        primitive = viewer.add_classification(self._positions())
        assert isinstance(primitive, cesiumkit.ClassificationPrimitive)
        html = viewer.to_html()
        assert "viewer.scene.primitives.add(new Cesium.ClassificationPrimitive({" in html

    def test_add_classification_with_options(self):
        viewer = cesiumkit.Viewer()
        viewer.add_classification(
            self._positions(),
            color=cesiumkit.Color(red=1.0, green=0.0, blue=0.0),
            classification_type=cesiumkit.ClassificationType.CESIUM_3D_TILE,
        )
        html = viewer.to_html()
        assert "classificationType: Cesium.ClassificationType.CESIUM_3D_TILE" in html


class TestClippingRenders:
    """Headless render checks: the generated JS must run, not just exist."""

    def _clipped_viewer(self):
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
        viewer.add_classification(
            [
                cesiumkit.Cartesian3FromDegrees(longitude=-74.02, latitude=40.70),
                cesiumkit.Cartesian3FromDegrees(longitude=-73.98, latitude=40.70),
                cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.74),
            ],
            color=cesiumkit.Color(red=0.0, green=0.6, blue=0.9, alpha=0.6),
        )
        return viewer

    def test_clipping_and_classification_render(self):
        from cesiumkit import _vendor

        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        from cesiumkit.testing import render_state

        state = render_state(self._clipped_viewer(), wait_ms=6000)
        assert not state["pageErrors"], state["pageErrors"]


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
