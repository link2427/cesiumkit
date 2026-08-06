"""Integration tests for full HTML output."""

import pytest
from pydantic import ValidationError

import cesiumkit


class TestFullHtmlOutput:
    def test_comprehensive_scene(self):
        """Test a comprehensive scene with multiple entity types."""
        viewer = cesiumkit.Viewer(
            ion_token="test_token",
            animation=False,
            timeline=False,
        )

        # Point entity
        viewer.add_entity(
            cesiumkit.Entity(
                name="Point",
                position=cesiumkit.Cartesian3.from_degrees(-75.59777, 40.03883, 100),
                point=cesiumkit.PointGraphics(
                    pixel_size=10,
                    color=cesiumkit.Color.RED,
                    outline_color=cesiumkit.Color.WHITE,
                    outline_width=2,
                ),
            )
        )

        # Polygon entity
        viewer.add_entity(
            cesiumkit.Entity(
                name="Polygon",
                polygon=cesiumkit.PolygonGraphics(
                    hierarchy=[
                        cesiumkit.Cartesian3.from_degrees(-115, 37),
                        cesiumkit.Cartesian3.from_degrees(-115, 32),
                        cesiumkit.Cartesian3.from_degrees(-107, 33),
                    ],
                    material=cesiumkit.Color.RED.with_alpha(0.5),
                    extruded_height=100000,
                    outline=True,
                    outline_color=cesiumkit.Color.BLACK,
                ),
            )
        )

        # Polyline entity
        viewer.add_entity(
            cesiumkit.Entity(
                name="Line",
                polyline=cesiumkit.PolylineGraphics(
                    positions=[
                        cesiumkit.Cartesian3.from_degrees(-75, 35),
                        cesiumkit.Cartesian3.from_degrees(-125, 35),
                    ],
                    width=5,
                    material=cesiumkit.PolylineGlowMaterial(
                        color=cesiumkit.Color.CYAN,
                        glow_power=0.2,
                    ),
                ),
            )
        )

        # Camera
        viewer.fly_to(
            cesiumkit.Cartesian3.from_degrees(-75.59777, 40.03883, 15000),
            duration=3.0,
        )

        html = viewer.to_html()

        # Verify structure
        assert "<!DOCTYPE html>" in html
        assert "Cesium.js" in html
        assert "widgets.css" in html
        assert "test_token" in html
        assert "Cesium.Viewer" in html
        assert html.count("viewer.entities.add") == 3
        assert "camera.flyTo" in html
        assert "fromDegrees" in html
        assert "pixelSize" in html
        assert "PolylineGlowMaterialProperty" in html

    def test_scene_with_datasources(self):
        viewer = cesiumkit.Viewer()
        viewer.load_geojson(url="https://example.com/data.geojson", clamp_to_ground=True)
        viewer.load_czml(url="https://example.com/data.czml")
        viewer.add_tileset(ion_asset_id=75343)

        html = viewer.to_html()
        assert "GeoJsonDataSource" in html
        assert "CzmlDataSource" in html
        assert "Cesium3DTileset" in html
        assert html.count("dataSources.add") == 2
        assert "primitives.add" in html

    def test_custom_data_source_with_entities(self):
        ds = cesiumkit.CustomDataSource(name="my_sources")
        ds.entities.add(
            cesiumkit.Entity(
                name="Custom",
                position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
                point=cesiumkit.PointGraphics(pixel_size=5),
            )
        )
        viewer = cesiumkit.Viewer()
        viewer.add_data_source(ds)
        html = viewer.to_html()
        assert 'var _ds = new Cesium.CustomDataSource("my_sources");' in html
        assert "viewer.dataSources.add(_ds);" in html
        assert "_ds.entities.add(" in html
        assert '"Custom"' in html

    def test_multiple_custom_data_sources_attach_to_their_own(self):
        """Each source's entity statement must run before the next source is declared."""
        viewer = cesiumkit.Viewer()
        for name, entity_name in (("source_a", "EntityA"), ("source_b", "EntityB")):
            ds = cesiumkit.CustomDataSource(name=name)
            ds.entities.add(
                cesiumkit.Entity(
                    name=entity_name,
                    position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
                    point=cesiumkit.PointGraphics(pixel_size=5),
                )
            )
            viewer.add_data_source(ds)
        html = viewer.to_html()
        assert html.count("var _ds = new Cesium.CustomDataSource(") == 2
        entity_a = html.index('"EntityA"')
        source_b_decl = html.index('var _ds = new Cesium.CustomDataSource("source_b")')
        entity_b = html.index('"EntityB"')
        assert entity_a < source_b_decl, "EntityA attached after source_b was declared"
        assert source_b_decl < entity_b, "EntityB attached before source_b was declared"

    def test_scene_with_globe_config(self):
        viewer = cesiumkit.Viewer(
            globe=cesiumkit.GlobeConfig(
                enable_lighting=True,
                depth_test_against_terrain=True,
            ),
        )
        html = viewer.to_html()
        assert "enableLighting = true" in html
        assert "depthTestAgainstTerrain = true" in html

    def test_show_sky_atmosphere_emitted(self):
        viewer = cesiumkit.Viewer(globe=cesiumkit.GlobeConfig(show_sky_atmosphere=False))
        html = viewer.to_html()
        assert "scene.skyAtmosphere.show = false" in html

    def test_scene_with_terrain_exaggeration(self):
        viewer = cesiumkit.Viewer(
            globe=cesiumkit.GlobeConfig(
                terrain_exaggeration=3.0,
                terrain_exaggeration_relative_height=100.0,
            )
        )
        html = viewer.to_html()
        assert "scene.verticalExaggeration = 3.0" in html
        assert "scene.verticalExaggerationRelativeHeight = 100.0" in html
        assert "globe.terrainExaggeration" not in html

    def test_terrain_exaggeration_validation(self):
        with pytest.raises(ValidationError):
            cesiumkit.GlobeConfig(terrain_exaggeration=-1)
        with pytest.raises(ValidationError):
            cesiumkit.GlobeConfig(terrain_exaggeration_relative_height=float("inf"))

    def test_scene_with_scene_config(self):
        viewer = cesiumkit.Viewer(
            scene=cesiumkit.SceneConfig(
                sky_box=False,
                fog_enabled=False,
            ),
        )
        html = viewer.to_html()
        assert "skyBox.show = false" in html
        assert "fog.enabled = false" in html

    def test_scene_config_render_mode(self):
        viewer = cesiumkit.Viewer(
            scene=cesiumkit.SceneConfig(
                request_render_mode=True,
                maximum_render_time_change=1.5,
            )
        )
        html = viewer.to_html()
        assert "scene.requestRenderMode = true" in html
        assert "scene.maximumRenderTimeChange = 1.5" in html

    def test_scene_config_fog_atmosphere_msaa(self):
        viewer = cesiumkit.Viewer(
            scene=cesiumkit.SceneConfig(
                fog_density=0.001,
                fog_minimum_brightness=0.2,
                fog_screen_space_error_factor=2.0,
                atmosphere_brightness_shift=0.1,
                atmosphere_hue_shift=0.2,
                atmosphere_saturation_shift=-0.1,
                msaa_samples=4,
            )
        )
        html = viewer.to_html()
        assert "scene.fog.density = 0.001" in html
        assert "scene.fog.minimumBrightness = 0.2" in html
        assert "scene.fog.screenSpaceErrorFactor = 2.0" in html
        assert "scene.skyAtmosphere.brightnessShift = 0.1" in html
        assert "scene.skyAtmosphere.hueShift = 0.2" in html
        assert "scene.skyAtmosphere.saturationShift = -0.1" in html
        assert "scene.msaaSamples = 4" in html

    def test_scene_config_validation(self):
        with pytest.raises(ValidationError):
            cesiumkit.SceneConfig(fog_density=0)
        with pytest.raises(ValidationError):
            cesiumkit.SceneConfig(fog_minimum_brightness=1.5)
        with pytest.raises(ValidationError):
            cesiumkit.SceneConfig(atmosphere_hue_shift=2)
        with pytest.raises(ValidationError):
            cesiumkit.SceneConfig(msaa_samples=0)
        with pytest.raises(ValidationError):
            # Cesium only accepts power-of-two sample counts
            cesiumkit.SceneConfig(msaa_samples=3)

    def test_viewer_shadow_options(self):
        viewer = cesiumkit.Viewer(
            scene3d_only=True,
            shadows=cesiumkit.ShadowMode.ENABLED,
            terrain_shadows=cesiumkit.ShadowMode.RECEIVE_ONLY,
        )
        html = viewer.to_html()
        assert "scene3DOnly: true" in html
        assert "shadows: Cesium.ShadowMode.ENABLED" in html
        assert "terrainShadows: Cesium.ShadowMode.RECEIVE_ONLY" in html

    def test_viewer_shadow_options_omitted_by_default(self):
        html = cesiumkit.Viewer().to_html()
        assert "scene3DOnly" not in html
        assert "terrainShadows" not in html

    def test_scene_options_render(self):
        from cesiumkit import _vendor

        if _vendor.vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        pytest.importorskip("playwright")
        from cesiumkit.testing import render_state

        viewer = cesiumkit.Viewer(
            scene3d_only=False,
            shadows=cesiumkit.ShadowMode.ENABLED,
            scene=cesiumkit.SceneConfig(
                fog_density=0.0002,
                fog_minimum_brightness=0.5,
                atmosphere_hue_shift=0.1,
                msaa_samples=4,
            ),
        )
        state = render_state(viewer, wait_ms=6000)
        assert not state["pageErrors"], state["pageErrors"]

    def test_post_process_configuration(self):
        viewer = cesiumkit.Viewer(
            scene=cesiumkit.SceneConfig(
                post_process=cesiumkit.PostProcessConfig(
                    bloom=cesiumkit.BloomConfig(enabled=True, contrast=100, step_size=4),
                    fxaa=cesiumkit.FXAAConfig(enabled=False),
                    ambient_occlusion=cesiumkit.AmbientOcclusionConfig(enabled=True, intensity=2),
                )
            )
        )
        html = viewer.to_html()
        assert "postProcessStages.bloom.enabled = true" in html
        assert "postProcessStages.bloom.uniforms.contrast = 100.0" in html
        assert "postProcessStages.bloom.uniforms.stepSize = 4.0" in html
        assert "postProcessStages.fxaa.enabled = false" in html
        assert "postProcessStages.ambientOcclusion.uniforms.intensity = 2.0" in html

    def test_disabled_post_process_does_not_write_uniforms(self):
        statements = cesiumkit.PostProcessConfig(
            bloom=cesiumkit.BloomConfig(enabled=False),
            ambient_occlusion=cesiumkit.AmbientOcclusionConfig(enabled=False),
        ).to_js_statements()
        assert statements == [
            "viewer.scene.postProcessStages.bloom.enabled = false;",
            "viewer.scene.postProcessStages.ambientOcclusion.enabled = false;",
        ]

    def test_post_process_validation(self):
        with pytest.raises(ValidationError):
            cesiumkit.BloomConfig(contrast=300)
        with pytest.raises(ValidationError):
            cesiumkit.AmbientOcclusionConfig(step_size=0)

    def test_time_dynamic_entity(self):
        pos = cesiumkit.SampledPositionProperty()
        pos.add_sample("2024-01-01T00:00:00Z", cesiumkit.Cartesian3.from_degrees(-75, 35, 100000))
        pos.add_sample("2024-01-01T06:00:00Z", cesiumkit.Cartesian3.from_degrees(-125, 35, 100000))

        viewer = cesiumkit.Viewer()
        viewer.add_entity(
            cesiumkit.Entity(
                name="Satellite",
                position=pos,
                point=cesiumkit.PointGraphics(pixel_size=8, color=cesiumkit.Color.WHITE),
                path=cesiumkit.PathGraphics(
                    width=2,
                    trail_time=3600,
                    material=cesiumkit.PolylineDashMaterial(color=cesiumkit.Color.CYAN),
                ),
            )
        )

        html = viewer.to_html()
        assert "SampledPositionProperty" in html
        assert "addSample" in html
        assert "trailTime" in html

    def test_no_deprecated_cesium_apis(self):
        """Generated HTML must only use Cesium 1.144-era APIs."""
        viewer = cesiumkit.Viewer(ion_token="tok")
        html = viewer.to_html()
        assert "imageryProvider:" not in html
        assert "new Cesium.CesiumTerrainProvider({" not in html
        assert "1.119" not in html
