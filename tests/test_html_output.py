"""Integration tests for full HTML output."""

import cesiumkit


class TestFullHtmlOutput:
    def test_comprehensive_scene(self):
        """Test a comprehensive scene with multiple entity types."""
        viewer = cesiumkit.Viewer(
            ion_token="test_token",
            animation=False,
            timeline=False,
            cesium_version="1.119",
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
