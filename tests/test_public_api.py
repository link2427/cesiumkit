"""Public API surface checks.

Every public module must declare ``__all__`` (the API audit contract), every
name it lists must actually exist, and every name *defined* in the module must
be listed. Names re-exported at the top level must resolve too.
"""

from __future__ import annotations

import importlib
import pathlib

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


# The 1.0 freeze. Everything cesiumkit exports at the top level, pinned as
# the stability contract: from 1.0 on, adding to or removing from this list
# is a breaking change and needs a major version bump (see CONTRIBUTING).
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
    "ClassificationType",
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
        "Surface changes are breaking changes past 1.0."
    )
