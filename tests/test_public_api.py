"""Public API surface checks.

Every public module must declare ``__all__`` (the API audit contract), every
name it lists must actually exist, and every name *defined* in the module must
be listed. Names re-exported at the top level must resolve too.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pathlib
import sys
import types

import pytest

import cesiumkit

PACKAGE_DIR = pathlib.Path(cesiumkit.__file__).resolve().parent

PUBLIC_MODULES = [
    "base",
    "camera",
    "clock",
    "clustering",
    "color",
    "coordinates",
    "czml",
    "datasources",
    "enums",
    "entities",
    "events",
    "gis",
    "globe",
    "imagery",
    "ion",
    "material",
    "math",
    "particle",
    "properties",
    "raster",
    "scene",
    "terrain",
    "testing",
    "utils",
    "viewer",
    "widget",
]

PUBLIC_ENTITY_MODULES = sorted(p.stem for p in (PACKAGE_DIR / "entities").glob("*.py") if not p.name.startswith("_"))


def _public_module_names() -> list[str]:
    return [f"cesiumkit.{m}" for m in PUBLIC_MODULES] + [f"cesiumkit.entities.{m}" for m in PUBLIC_ENTITY_MODULES]


def _import_checked(module_name: str):
    """Import a module, skipping when an optional dependency is absent."""
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        pytest.skip(f"optional dependency missing for {module_name}: {exc}")


def _declared_all(module_name: str) -> tuple[str, ...]:
    """Read ``__all__`` without importing an optional-dependency module."""
    try:
        return tuple(importlib.import_module(module_name).__all__)
    except ImportError:
        if module_name != "cesiumkit.widget":
            raise
        relative = module_name.removeprefix("cesiumkit.").split(".")
        module_path = PACKAGE_DIR.joinpath(*relative)
        source_path = module_path / "__init__.py" if module_path.is_dir() else module_path.with_suffix(".py")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                return tuple(ast.literal_eval(node.value))
        raise AssertionError(f"{module_name} must declare a literal __all__")


# 1.0 API contract. Keep the declaration order as well as membership: it is
# what users see in ``from module import *`` and in generated API listings.
GOLDEN_MODULE_ALL = {
    "cesiumkit": tuple(
        """__version__ CesiumBase CesiumEnum JsCode generate_id Cartesian2 Cartesian3 Cartesian3FromDegrees
        Cartesian3FromRadians Cartesian3DegreesArray Cartesian3DegreesArrayHeights Cartographic
        CartographicFromDegrees BoundingSphere RectangleCoords RectangleCoordsFromDegrees NearFarScalar
        DistanceDisplayCondition HeadingPitchRoll HeadingPitchRollFromDegrees HeadingPitchRange Quaternion Matrix3
        Matrix4 Color HeightReference HorizontalOrigin VerticalOrigin LabelStyle ClassificationType SceneMode
        ShadowMode ColorBlendMode ArcType CornerType ClockRange ClockStep ScreenSpaceEventType StripeOrientation
        MaterialBase SolidColorMaterial ImageMaterial GridMaterial StripeMaterial CheckerboardMaterial
        PolylineGlowMaterial PolylineArrowMaterial PolylineDashMaterial PolylineOutlineMaterial Entity EntityGraphics
        EntityCollection BillboardGraphics BoxGraphics CorridorGraphics CylinderGraphics EllipseGraphics
        EllipsoidGraphics LabelGraphics ModelGraphics PathGraphics Plane PlaneGraphics ParticleSystem PointGraphics
        PolygonGraphics PolygonHierarchy PolylineGraphics PolylineVolumeGraphics RectangleGraphics WallGraphics
        Cesium3DTilesetGraphics JulianDate ClockConfig ConstantProperty SampledProperty SampledPositionProperty
        TimeIntervalCollectionProperty CallbackProperty ReferenceProperty CzmlDataSource GeoJsonDataSource
        KmlDataSource CustomDataSource ImageryProvider IonImageryProvider BingMapsImageryProvider
        TileMapServiceImageryProvider UrlTemplateImageryProvider WebMapServiceImageryProvider
        WebMapTileServiceImageryProvider SingleTileImageryProvider TerrainProvider EllipsoidTerrainProvider
        CesiumTerrainProvider IonTerrainProvider WmsTerrainProvider WmtsTerrainProvider Camera CameraPosition
        FlyToOptions LookAtOptions AmbientOcclusionConfig BloomConfig ClassificationPrimitive ClippingPlane
        ClippingPlaneCollection FXAAConfig PostProcessConfig SceneConfig GlobeConfig Ion IonResource Cesium3DTileset
        Cesium3DTileStyle EntityClusterConfig EventHandler CzmlDocument geodataframe_to_entities dataframe_to_entities
        geodataframe_to_czml_packets RasterSource aggregate_points_to_raster Viewer""".split()
    ),
    "cesiumkit.base": ("CesiumBase", "CesiumEnum"),
    "cesiumkit.camera": ("Camera", "CameraPosition", "FlyToOptions", "LookAtOptions"),
    "cesiumkit.clock": ("ClockConfig", "JulianDate"),
    "cesiumkit.clustering": ("EntityClusterConfig",),
    "cesiumkit.color": tuple(
        """ALICEBLUE ANTIQUEWHITE AQUA AQUAMARINE AZURE BEIGE BISQUE BLACK BLANCHEDALMOND BLUE BLUEVIOLET
        BROWN BURLYWOOD CADETBLUE CHARTREUSE CHOCOLATE CORAL CORNFLOWERBLUE CORNSILK CRIMSON CYAN Color DARKBLUE
        DARKCYAN DARKGOLDENROD DARKGRAY DARKGREEN DARKGREY DARKKHAKI DARKMAGENTA DARKOLIVEGREEN DARKORANGE
        DARKORCHID DARKRED DARKSALMON DARKSEAGREEN DARKSLATEBLUE DARKSLATEGRAY DARKSLATEGREY DARKTURQUOISE
        DARKVIOLET DEEPPINK DEEPSKYBLUE DIMGRAY DIMGREY DODGERBLUE FIREBRICK FLORALWHITE FORESTGREEN FUCHSIA
        GAINSBORO GHOSTWHITE GOLD GOLDENROD GRAY GREEN GREENYELLOW GREY HONEYDEW HOTPINK INDIANRED INDIGO IVORY
        KHAKI LAVENDER LAVENDERBLUSH LAWNGREEN LEMONCHIFFON LIGHTBLUE LIGHTCORAL LIGHTCYAN LIGHTGOLDENRODYELLOW
        LIGHTGRAY LIGHTGREEN LIGHTGREY LIGHTPINK LIGHTSALMON LIGHTSEAGREEN LIGHTSKYBLUE LIGHTSLATEGRAY
        LIGHTSLATEGREY LIGHTSTEELBLUE LIGHTYELLOW LIME LIMEGREEN LINEN MAGENTA MAROON MEDIUMAQUAMARINE MEDIUMBLUE
        MEDIUMORCHID MEDIUMPURPLE MEDIUMSEAGREEN MEDIUMSLATEBLUE MEDIUMSPRINGGREEN MEDIUMTURQUOISE
        MEDIUMVIOLETRED MIDNIGHTBLUE MINTCREAM MISTYROSE MOCCASIN NAVAJOWHITE NAVY OLDLACE OLIVE OLIVEDRAB ORANGE
        ORANGERED ORCHID PALEGOLDENROD PALEGREEN PALETURQUOISE PALEVIOLETRED PAPAYAWHIP PEACHPUFF PERU PINK PLUM
        POWDERBLUE PURPLE RED ROSYBROWN ROYALBLUE SADDLEBROWN SALMON SANDYBROWN SEAGREEN SEASHELL SIENNA SILVER
        SKYBLUE SLATEBLUE SLATEGRAY SLATEGREY SNOW SPRINGGREEN STEELBLUE TAN TEAL THISTLE TOMATO TRANSPARENT
        TURQUOISE VIOLET WHEAT WHITE WHITESMOKE YELLOW YELLOWGREEN""".split()
    ),
    "cesiumkit.coordinates": (
        "BoundingSphere",
        "Cartesian2",
        "Cartesian3",
        "Cartesian3DegreesArray",
        "Cartesian3DegreesArrayHeights",
        "Cartesian3FromDegrees",
        "Cartesian3FromRadians",
        "Cartographic",
        "CartographicFromDegrees",
        "DistanceDisplayCondition",
        "NearFarScalar",
        "RectangleCoords",
        "RectangleCoordsFromDegrees",
    ),
    "cesiumkit.czml": ("CzmlDocument",),
    "cesiumkit.datasources": ("CustomDataSource", "CzmlDataSource", "DataSource", "GeoJsonDataSource", "KmlDataSource"),
    "cesiumkit.enums": (
        "ArcType",
        "ClassificationType",
        "ClockRange",
        "ClockStep",
        "ColorBlendMode",
        "CornerType",
        "HeightReference",
        "HorizontalOrigin",
        "LabelStyle",
        "SceneMode",
        "ScreenSpaceEventType",
        "ShadowMode",
        "StripeOrientation",
        "VerticalOrigin",
    ),
    "cesiumkit.entities": tuple(
        """Entity EntityCollection EntityGraphics BillboardGraphics BoxGraphics CorridorGraphics CylinderGraphics
        EllipseGraphics EllipsoidGraphics LabelGraphics ModelGraphics PathGraphics Plane PlaneGraphics PointGraphics
        PolygonGraphics PolygonHierarchy PolylineGraphics PolylineVolumeGraphics RectangleGraphics
        Cesium3DTilesetGraphics WallGraphics""".split()
    ),
    "cesiumkit.events": ("EventHandler",),
    "cesiumkit.gis": ("dataframe_to_entities", "geodataframe_to_czml_packets", "geodataframe_to_entities"),
    "cesiumkit.globe": ("GlobeConfig",),
    "cesiumkit.imagery": (
        "BingMapsImageryProvider",
        "ImageryProvider",
        "IonImageryProvider",
        "SingleTileImageryProvider",
        "TileMapServiceImageryProvider",
        "UrlTemplateImageryProvider",
        "WebMapServiceImageryProvider",
        "WebMapTileServiceImageryProvider",
    ),
    "cesiumkit.ion": ("Cesium3DTileStyle", "Cesium3DTileset", "Ion", "IonResource"),
    "cesiumkit.material": (
        "CheckerboardMaterial",
        "GridMaterial",
        "ImageMaterial",
        "MaterialBase",
        "PolylineArrowMaterial",
        "PolylineDashMaterial",
        "PolylineGlowMaterial",
        "PolylineOutlineMaterial",
        "SolidColorMaterial",
        "StripeMaterial",
    ),
    "cesiumkit.math": (
        "HeadingPitchRange",
        "HeadingPitchRoll",
        "HeadingPitchRollFromDegrees",
        "Matrix3",
        "Matrix4",
        "Quaternion",
    ),
    "cesiumkit.particle": ("ParticleSystem",),
    "cesiumkit.properties": (
        "CallbackProperty",
        "ConstantProperty",
        "PropertyBase",
        "ReferenceProperty",
        "SampledPositionProperty",
        "SampledProperty",
        "TimeIntervalCollectionProperty",
    ),
    "cesiumkit.raster": ("RasterSource", "RasterRenderError", "aggregate_points_to_raster"),
    "cesiumkit.scene": (
        "AmbientOcclusionConfig",
        "BloomConfig",
        "ClassificationPrimitive",
        "ClippingPlane",
        "ClippingPlaneCollection",
        "FXAAConfig",
        "PostProcessConfig",
        "SceneConfig",
    ),
    "cesiumkit.terrain": (
        "CesiumTerrainProvider",
        "EllipsoidTerrainProvider",
        "IonTerrainProvider",
        "TerrainProvider",
        "WmsTerrainProvider",
        "WmtsTerrainProvider",
    ),
    "cesiumkit.testing": (
        "DEFAULT_VIEWPORT",
        "DEFAULT_WAIT_MS",
        "render_screenshot",
        "render_state",
        "serve",
        "start_server",
    ),
    "cesiumkit.utils": ("JsCode", "generate_id"),
    "cesiumkit.viewer": ("Viewer",),
    "cesiumkit.widget": ("CesiumKitWidget",),
    "cesiumkit.entities.billboard": ("BillboardGraphics",),
    "cesiumkit.entities.box": ("BoxGraphics",),
    "cesiumkit.entities.corridor": ("CorridorGraphics",),
    "cesiumkit.entities.cylinder": ("CylinderGraphics",),
    "cesiumkit.entities.ellipse": ("EllipseGraphics",),
    "cesiumkit.entities.ellipsoid": ("EllipsoidGraphics",),
    "cesiumkit.entities.label": ("LabelGraphics",),
    "cesiumkit.entities.model": ("ModelGraphics",),
    "cesiumkit.entities.path": ("PathGraphics",),
    "cesiumkit.entities.plane": ("Plane", "PlaneGraphics"),
    "cesiumkit.entities.point": ("PointGraphics",),
    "cesiumkit.entities.polygon": ("PolygonGraphics", "PolygonHierarchy"),
    "cesiumkit.entities.polyline": ("PolylineGraphics",),
    "cesiumkit.entities.polyline_volume": ("PolylineVolumeGraphics",),
    "cesiumkit.entities.rectangle": ("RectangleGraphics",),
    "cesiumkit.entities.tileset": ("Cesium3DTilesetGraphics",),
    "cesiumkit.entities.wall": ("WallGraphics",),
}


def test_every_public_module_all_is_frozen() -> None:
    expected_modules = {"cesiumkit", *_public_module_names()}
    assert set(GOLDEN_MODULE_ALL) == expected_modules
    for module_name, expected in GOLDEN_MODULE_ALL.items():
        assert _declared_all(module_name) == expected, f"{module_name}.__all__ changed"


@pytest.mark.parametrize("module_name", _public_module_names())
def test_module_declares_all(module_name: str) -> None:
    mod = _import_checked(module_name)
    assert hasattr(mod, "__all__"), f"{module_name} must declare __all__"
    assert mod.__all__, f"{module_name} __all__ must not be empty"
    for name in mod.__all__:
        assert hasattr(mod, name), f"{module_name}.{name} listed in __all__ but missing"
        assert not name.startswith("_"), f"{module_name} __all__ contains private name {name}"


@pytest.mark.parametrize("module_name", _public_module_names())
def test_all_covers_all_defined_names(module_name: str) -> None:
    """Every name defined in the module (classes/functions) must be in __all__."""
    mod = _import_checked(module_name)
    defined = {
        name
        for name, obj in vars(mod).items()
        if not name.startswith("_") and getattr(obj, "__module__", None) == mod.__name__
    }
    missing = defined - set(mod.__all__)
    assert not missing, f"{module_name} defines public names not in __all__: {sorted(missing)}"


def test_top_level_all_resolves() -> None:
    for name in cesiumkit.__all__:
        assert hasattr(cesiumkit, name), f"cesiumkit.{name} listed in __all__ but missing"


def test_lazy_widget_export_does_not_require_widget_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """The optional widget is imported only when its top-level name is read."""
    fake_widget = types.ModuleType("cesiumkit.widget")

    class FakeWidget:
        pass

    fake_widget.CesiumKitWidget = FakeWidget
    monkeypatch.delitem(sys.modules, "cesiumkit.widget", raising=False)
    monkeypatch.setitem(sys.modules, "cesiumkit.widget", fake_widget)

    assert "CesiumKitWidget" not in cesiumkit.__all__
    assert cesiumkit.CesiumKitWidget is FakeWidget


CRITICAL_SIGNATURES = {
    "Viewer": {
        "target": cesiumkit.Viewer,
        "parameters": (
            "ion_token",
            "container_id",
            "width",
            "height",
            "title",
            "animation",
            "base_layer_picker",
            "fullscreen_button",
            "vr_button",
            "geocoder",
            "home_button",
            "info_box",
            "scene_mode_picker",
            "selection_indicator",
            "timeline",
            "navigation_help_button",
            "navigation_instructions_initially_visible",
            "request_render_mode",
            "maximum_render_time_change",
            "resolution_scale",
            "target_frame_rate",
            "show_renderer_errors",
            "scene_mode",
            "scene3d_only",
            "shadows",
            "terrain_shadows",
            "scene",
            "globe",
            "terrain_provider",
            "imagery_provider",
            "clock",
            "should_animate",
            "camera",
            "clustering",
        ),
        "keyword_only": (),
        "defaults": {"container_id": "cesiumContainer", "width": "100%", "height": "100%", "title": "cesiumkit"},
    },
    "Viewer.show": {
        "target": cesiumkit.Viewer.show,
        "parameters": ("self", "port", "open_browser"),
        "keyword_only": (),
        "defaults": {"port": 0, "open_browser": True},
    },
    "Viewer.close": {
        "target": cesiumkit.Viewer.close,
        "parameters": ("self",),
        "keyword_only": (),
        "defaults": {},
    },
    "Viewer.add_raster": {
        "target": cesiumkit.Viewer.add_raster,
        "parameters": ("self", "source", "name", "opacity", "maximum_level"),
        "keyword_only": ("name", "opacity", "maximum_level"),
        "defaults": {"name": None, "opacity": 1.0, "maximum_level": None},
    },
    "Viewer.add_wmts_layer": {
        "target": cesiumkit.Viewer.add_wmts_layer,
        "parameters": ("self", "url", "layer", "style", "tile_matrix_set", "format", "maximum_level", "opacity"),
        "keyword_only": ("style", "tile_matrix_set", "format", "maximum_level", "opacity"),
        "defaults": {
            "style": "",
            "tile_matrix_set": "default",
            "format": "image/png",
            "maximum_level": None,
            "opacity": 1.0,
        },
    },
    "Viewer.add_points": {
        "target": cesiumkit.Viewer.add_points,
        "parameters": ("self", "gdf", "aggregation", "colormap", "plot_width", "plot_height", "kwargs"),
        "keyword_only": ("aggregation", "colormap", "plot_width", "plot_height"),
        "defaults": {"aggregation": True, "colormap": None, "plot_width": 1024, "plot_height": 512},
    },
    "Viewer.to_widget": {
        "target": cesiumkit.Viewer.to_widget,
        "parameters": ("self", "height", "cesium_version"),
        "keyword_only": ("height", "cesium_version"),
        "defaults": {"height": "600px", "cesium_version": None},
    },
    "Viewer.add_classification": {
        "target": cesiumkit.Viewer.add_classification,
        "parameters": (
            "self",
            "positions",
            "color",
            "height",
            "extruded_height",
            "classification_type",
        ),
        "keyword_only": ("color", "height", "extruded_height", "classification_type"),
        "defaults": {
            "color": None,
            "height": 0.0,
            "extruded_height": 100_000.0,
            "classification_type": None,
        },
    },
    "RasterSource": {
        "target": cesiumkit.RasterSource,
        "parameters": ("source", "name", "tile_cache_size"),
        "keyword_only": ("name", "tile_cache_size"),
        "defaults": {"name": None, "tile_cache_size": 512},
    },
    "aggregate_points_to_raster": {
        "target": cesiumkit.aggregate_points_to_raster,
        "parameters": ("gdf", "plot_width", "plot_height", "colormap"),
        "keyword_only": ("plot_width", "plot_height", "colormap"),
        "defaults": {"plot_width": 1024, "plot_height": 512, "colormap": None},
    },
    "Cesium3DTileset": {
        "target": cesiumkit.Cesium3DTileset,
        "parameters": (
            "url",
            "ion_asset_id",
            "show",
            "maximum_screen_space_error",
            "cache_bytes",
            "maximum_memory_usage",
            "shadows",
            "style",
            "clipping_planes",
        ),
        "keyword_only": (
            "url",
            "ion_asset_id",
            "show",
            "maximum_screen_space_error",
            "cache_bytes",
            "maximum_memory_usage",
            "shadows",
            "style",
            "clipping_planes",
        ),
        "defaults": {
            "url": None,
            "ion_asset_id": None,
            "show": True,
            "maximum_screen_space_error": 16.0,
            "cache_bytes": None,
            "maximum_memory_usage": None,
        },
    },
    "IonImageryProvider": {
        "target": cesiumkit.IonImageryProvider,
        "parameters": ("asset_id", "access_token", "server"),
        "keyword_only": ("asset_id", "access_token", "server"),
        "defaults": {"access_token": None, "server": None},
    },
}


def test_critical_signatures_are_frozen() -> None:
    for label, expected in CRITICAL_SIGNATURES.items():
        signature = inspect.signature(expected["target"])
        assert tuple(signature.parameters) == expected["parameters"], label
        assert (
            tuple(
                name
                for name, parameter in signature.parameters.items()
                if parameter.kind is inspect.Parameter.KEYWORD_ONLY
            )
            == expected["keyword_only"]
        ), label
        for name, value in expected["defaults"].items():
            assert signature.parameters[name].default == value, f"{label}.{name} default changed"


# The 1.0 freeze. Everything cesiumkit exports at the top level, pinned as
# the stability contract. Every delta needs intentional compatibility review;
# removals and incompatible changes require a major version bump, while a
# compatible addition does not automatically do so (see CONTRIBUTING).
# This list is the 0.9 surface minus the two 0.8-deprecated names that were
# removed at 1.0 (OpenStreetMapImageryProvider; the cesium_version argument
# was a constructor parameter, not an export).
GOLDEN_TOP_LEVEL_SURFACE = {
    "AmbientOcclusionConfig",
    "ArcType",
    "BillboardGraphics",
    "BingMapsImageryProvider",
    "BloomConfig",
    "BoundingSphere",
    "BoxGraphics",
    "CallbackProperty",
    "Camera",
    "CameraPosition",
    "Cartesian2",
    "Cartesian3",
    "Cartesian3DegreesArray",
    "Cartesian3DegreesArrayHeights",
    "Cartesian3FromDegrees",
    "Cartesian3FromRadians",
    "Cartographic",
    "CartographicFromDegrees",
    "Cesium3DTileStyle",
    "Cesium3DTileset",
    "Cesium3DTilesetGraphics",
    "CesiumBase",
    "CesiumEnum",
    "CesiumTerrainProvider",
    "CheckerboardMaterial",
    "ClassificationPrimitive",
    "ClassificationType",
    "ClippingPlane",
    "ClippingPlaneCollection",
    "ClockConfig",
    "ClockRange",
    "ClockStep",
    "Color",
    "ColorBlendMode",
    "ConstantProperty",
    "CornerType",
    "CorridorGraphics",
    "CustomDataSource",
    "CylinderGraphics",
    "CzmlDataSource",
    "CzmlDocument",
    "DistanceDisplayCondition",
    "EllipseGraphics",
    "EllipsoidGraphics",
    "EllipsoidTerrainProvider",
    "Entity",
    "EntityClusterConfig",
    "EntityCollection",
    "EntityGraphics",
    "EventHandler",
    "FXAAConfig",
    "FlyToOptions",
    "GeoJsonDataSource",
    "GlobeConfig",
    "GridMaterial",
    "HeadingPitchRange",
    "HeadingPitchRoll",
    "HeadingPitchRollFromDegrees",
    "HeightReference",
    "HorizontalOrigin",
    "ImageMaterial",
    "ImageryProvider",
    "Ion",
    "IonImageryProvider",
    "IonResource",
    "IonTerrainProvider",
    "JsCode",
    "JulianDate",
    "KmlDataSource",
    "LabelGraphics",
    "LabelStyle",
    "LookAtOptions",
    "MaterialBase",
    "Matrix3",
    "Matrix4",
    "ModelGraphics",
    "NearFarScalar",
    "ParticleSystem",
    "PathGraphics",
    "Plane",
    "PlaneGraphics",
    "PointGraphics",
    "PolygonGraphics",
    "PolygonHierarchy",
    "PolylineArrowMaterial",
    "PolylineDashMaterial",
    "PolylineGlowMaterial",
    "PolylineGraphics",
    "PolylineOutlineMaterial",
    "PolylineVolumeGraphics",
    "PostProcessConfig",
    "Quaternion",
    "RasterSource",
    "RectangleCoords",
    "RectangleCoordsFromDegrees",
    "RectangleGraphics",
    "ReferenceProperty",
    "SampledPositionProperty",
    "SampledProperty",
    "SceneConfig",
    "SceneMode",
    "ScreenSpaceEventType",
    "ShadowMode",
    "SingleTileImageryProvider",
    "SolidColorMaterial",
    "StripeMaterial",
    "StripeOrientation",
    "TerrainProvider",
    "TileMapServiceImageryProvider",
    "TimeIntervalCollectionProperty",
    "UrlTemplateImageryProvider",
    "VerticalOrigin",
    "Viewer",
    "WallGraphics",
    "WebMapServiceImageryProvider",
    "WebMapTileServiceImageryProvider",
    "WmsTerrainProvider",
    "WmtsTerrainProvider",
    "__version__",
    "aggregate_points_to_raster",
    "dataframe_to_entities",
    "generate_id",
    "geodataframe_to_czml_packets",
    "geodataframe_to_entities",
}


def test_top_level_surface_is_frozen() -> None:
    """The exported surface must match the 1.0 golden list exactly."""
    actual = set(cesiumkit.__all__)
    assert actual == GOLDEN_TOP_LEVEL_SURFACE, (
        "cesiumkit's top-level surface changed since 1.0. "
        f"added: {sorted(actual - GOLDEN_TOP_LEVEL_SURFACE)}; "
        f"removed: {sorted(GOLDEN_TOP_LEVEL_SURFACE - actual)}. "
        "Review additions for compatibility; removals or incompatible changes require a major release."
    )
