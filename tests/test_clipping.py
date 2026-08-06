"""Tests for 3D Tiles clipping and model/globe clipping planes."""

import io
import math

import pytest
from pydantic import ValidationError

import cesiumkit


class TestClippingPlane:
    def test_to_js(self):
        plane = cesiumkit.ClippingPlane(
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
            distance=12.5,
        )
        assert plane.to_js() == ("new Cesium.ClippingPlane(new Cesium.Cartesian3(0.0, 0.0, 1.0), 12.5)")

    def test_from_point_normal(self):
        plane = cesiumkit.ClippingPlane.from_point_normal(
            point=cesiumkit.Cartesian3(x=0, y=0, z=10),
            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
        )
        assert plane.distance == -10.0

    def test_normal_and_distance_required(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClippingPlane(normal=cesiumkit.Cartesian3(x=0, y=0, z=1))

    @pytest.mark.parametrize(
        "normal",
        [
            cesiumkit.Cartesian3(x=0, y=0, z=0),
            cesiumkit.Cartesian3(x=0, y=0, z=2),
            cesiumkit.Cartesian3FromDegrees(longitude=-74.0, latitude=40.7),
        ],
    )
    def test_normal_must_be_a_unit_vector(self, normal):
        with pytest.raises(ValidationError, match="normal"):
            cesiumkit.ClippingPlane(normal=normal, distance=0)

    def test_distance_must_be_finite(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClippingPlane(
                normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                distance=float("inf"),
            )


class TestClippingPlaneCollection:
    def _collection(self, **kwargs):
        return cesiumkit.ClippingPlaneCollection(
            planes=[
                cesiumkit.ClippingPlane(
                    normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                    distance=0,
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
        assert "unionClippingRegions: true" in self._collection(union_clipping_regions=True).to_js()

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
        assert "geometry: Cesium.PolygonGeometry.fromPositions({" in js
        assert "Cesium.Cartesian3.fromDegrees(-74.02, 40.7)" in js
        assert "height: 0.0" in js
        assert "extrudedHeight: 100000.0" in js
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

    def test_to_js_css_string_color(self):
        js = cesiumkit.ClassificationPrimitive(
            positions=self._positions(),
            color="#ff8800",
        ).to_js()
        # the hex string becomes a concrete Color, never fromColor("...")
        assert "fromColor(new Cesium.Color(1.0, 0.5333333333333333, 0.0, 1.0))" in js
        assert 'fromColor("' not in js

    def test_non_hex_color_string_rejected(self):
        with pytest.raises(ValueError):
            cesiumkit.ClassificationPrimitive(positions=self._positions(), color="red").to_js()

    def test_unsupported_color_type_rejected(self):
        with pytest.raises(TypeError):
            cesiumkit.ClassificationPrimitive(positions=self._positions(), color=(1.0, 0.0, 0.0)).to_js()

    def test_too_few_positions_rejected(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClassificationPrimitive(
                positions=[
                    cesiumkit.Cartesian3(x=0, y=0, z=0),
                    cesiumkit.Cartesian3(x=1, y=0, z=0),
                ]
            )

    def test_non_finite_height_rejected(self):
        with pytest.raises(ValidationError):
            cesiumkit.ClassificationPrimitive(
                positions=[
                    cesiumkit.Cartesian3(x=0, y=0, z=0),
                    cesiumkit.Cartesian3(x=1, y=0, z=0),
                    cesiumkit.Cartesian3(x=0, y=1, z=0),
                ],
                height=float("inf"),
            )

    def test_classification_volume_must_have_distinct_faces(self):
        with pytest.raises(ValidationError, match="height and extruded_height must differ"):
            cesiumkit.ClassificationPrimitive(
                positions=self._positions(),
                height=50.0,
                extruded_height=50.0,
            )

    def test_assignment_cannot_make_classification_volume_degenerate(self):
        primitive = cesiumkit.ClassificationPrimitive(positions=self._positions())
        with pytest.raises(ValidationError, match="height and extruded_height must differ"):
            primitive.height = primitive.extruded_height
        assert primitive.height == 0.0
        assert primitive.extruded_height == 100_000.0

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
            height=-100.0,
            extruded_height=5_000.0,
            classification_type=cesiumkit.ClassificationType.CESIUM_3D_TILE,
        )
        html = viewer.to_html()
        assert "height: -100.0" in html
        assert "extrudedHeight: 5000.0" in html
        assert "classificationType: Cesium.ClassificationType.CESIUM_3D_TILE" in html


class TestClippingRenders:
    """Headless render checks: the generated JS must run, not just exist."""

    def _clipped_viewer(self):
        viewer = cesiumkit.Viewer(
            globe=cesiumkit.GlobeConfig(
                clipping_planes=cesiumkit.ClippingPlaneCollection(
                    planes=[
                        cesiumkit.ClippingPlane(
                            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                            distance=0,
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
        pytest.importorskip("playwright")
        from cesiumkit.testing import render_state

        state = render_state(self._clipped_viewer(), wait_ms=6000)
        assert not state["pageErrors"], state["pageErrors"]

    def test_classification_changes_rendered_pixels(self, playwright_browser):
        from PIL import Image, ImageChops

        from cesiumkit.testing import serve

        viewer = cesiumkit.Viewer(request_render_mode=True)
        viewer.add_classification(
            [
                cesiumkit.Cartesian3FromDegrees(longitude=-74.02, latitude=40.70),
                cesiumkit.Cartesian3FromDegrees(longitude=-73.98, latitude=40.70),
                cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.74),
            ],
            color=cesiumkit.Color(red=1.0, green=0.0, blue=1.0),
        )
        viewer.set_view(
            cesiumkit.Cartesian3FromDegrees(longitude=-74.00, latitude=40.72, height=20_000),
            orientation={"heading": 0.0, "pitch": -math.pi / 2, "roll": 0.0},
        )

        errors: list[str] = []
        with serve(viewer) as url:
            page = playwright_browser.new_page(viewport={"width": 800, "height": 600})
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            try:
                page.goto(url, wait_until="load")
                page.wait_for_function(
                    """() => {
                        const primitives = [];
                        for (let i = 0; i < viewer.scene.primitives.length; i++) {
                            const primitive = viewer.scene.primitives.get(i);
                            if (primitive instanceof Cesium.ClassificationPrimitive) primitives.push(primitive);
                        }
                        return primitives.length === 1 && primitives[0].ready && viewer.scene.globe.tilesLoaded;
                    }""",
                    timeout=15_000,
                )
                page.wait_for_timeout(500)
                shown = page.screenshot()
                page.evaluate(
                    """() => {
                        for (let i = 0; i < viewer.scene.primitives.length; i++) {
                            const primitive = viewer.scene.primitives.get(i);
                            if (primitive instanceof Cesium.ClassificationPrimitive) primitive.show = false;
                        }
                        viewer.scene.requestRender();
                    }"""
                )
                page.wait_for_timeout(500)
                hidden = page.screenshot()
            finally:
                page.close()

        assert errors == []
        difference = ImageChops.difference(Image.open(io.BytesIO(shown)), Image.open(io.BytesIO(hidden))).convert("RGB")
        histogram = difference.histogram()
        changed_channels = sum(sum(histogram[start + 1 : start + 256]) for start in (0, 256, 512))
        assert changed_channels > 1_000


class TestClippingWiring:
    def test_tileset_clipping_planes(self):
        tileset = cesiumkit.Cesium3DTileset(
            url="https://example.com/tileset.json",
            clipping_planes=cesiumkit.ClippingPlaneCollection(
                planes=[
                    cesiumkit.ClippingPlane(
                        normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                        distance=0,
                    )
                ]
            ),
        )
        js = tileset.to_js()
        assert "clippingPlanes: new Cesium.ClippingPlaneCollection({" in js
        assert "new Cesium.ClippingPlane(new Cesium.Cartesian3(0.0, 0.0, 1.0), 0.0)" in js

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
                            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                            distance=0,
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
                            normal=cesiumkit.Cartesian3(x=0, y=0, z=1),
                            distance=0,
                        )
                    ]
                )
            )
        )
        html = viewer.to_html()
        assert "scene.globe.clippingPlanes = new Cesium.ClippingPlaneCollection({" in html
