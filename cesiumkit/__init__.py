"""cesiumkit: Object-oriented Python interface for CesiumJS 3D geospatial visualization."""

from cesiumkit import color as _color_module
from cesiumkit._version import __version__

# Core
from cesiumkit.base import CesiumBase, CesiumEnum

# Color
from cesiumkit.color import Color

# Coordinates & Math
from cesiumkit.coordinates import (
    BoundingSphere,
    Cartesian2,
    Cartesian3,
    Cartesian3DegreesArray,
    Cartesian3DegreesArrayHeights,
    Cartesian3FromDegrees,
    Cartesian3FromRadians,
    Cartographic,
    CartographicFromDegrees,
    DistanceDisplayCondition,
    NearFarScalar,
    RectangleCoords,
    RectangleCoordsFromDegrees,
)
from cesiumkit.math import (
    HeadingPitchRange,
    HeadingPitchRoll,
    HeadingPitchRollFromDegrees,
    Matrix3,
    Matrix4,
    Quaternion,
)
from cesiumkit.utils import JsCode, generate_id

# Camera
from cesiumkit.camera import Camera, CameraPosition, FlyToOptions, LookAtOptions

# Time & Properties
from cesiumkit.clock import ClockConfig, JulianDate

# CZML
from cesiumkit.czml import CzmlDocument

# Data Sources
from cesiumkit.datasources import (
    CustomDataSource,
    CzmlDataSource,
    GeoJsonDataSource,
    KmlDataSource,
)

# Entities
from cesiumkit.entities._base import Entity, EntityCollection, EntityGraphics
from cesiumkit.entities.billboard import BillboardGraphics
from cesiumkit.entities.box import BoxGraphics
from cesiumkit.entities.corridor import CorridorGraphics
from cesiumkit.entities.cylinder import CylinderGraphics
from cesiumkit.entities.ellipse import EllipseGraphics
from cesiumkit.entities.ellipsoid import EllipsoidGraphics
from cesiumkit.entities.label import LabelGraphics
from cesiumkit.entities.model import ModelGraphics
from cesiumkit.entities.path import PathGraphics
from cesiumkit.entities.point import PointGraphics
from cesiumkit.entities.polygon import PolygonGraphics, PolygonHierarchy
from cesiumkit.entities.polyline import PolylineGraphics
from cesiumkit.entities.polyline_volume import PolylineVolumeGraphics
from cesiumkit.entities.rectangle import RectangleGraphics
from cesiumkit.entities.tileset import Cesium3DTilesetGraphics
from cesiumkit.entities.wall import WallGraphics
from cesiumkit.enums import (
    ArcType,
    ClassificationType,
    ClockRange,
    ClockStep,
    ColorBlendMode,
    CornerType,
    HeightReference,
    HorizontalOrigin,
    LabelStyle,
    SceneMode,
    ScreenSpaceEventType,
    ShadowMode,
    StripeOrientation,
    VerticalOrigin,
)

# Events
from cesiumkit.events import EventHandler
from cesiumkit.globe import GlobeConfig

# Imagery Providers
from cesiumkit.imagery import (
    BingMapsImageryProvider,
    ImageryProvider,
    IonImageryProvider,
    OpenStreetMapImageryProvider,
    SingleTileImageryProvider,
    TileMapServiceImageryProvider,
    UrlTemplateImageryProvider,
    WebMapServiceImageryProvider,
    WebMapTileServiceImageryProvider,
)

# Ion
from cesiumkit.ion import Cesium3DTileset, Ion, IonResource

# Materials
from cesiumkit.material import (
    CheckerboardMaterial,
    GridMaterial,
    ImageMaterial,
    MaterialBase,
    PolylineArrowMaterial,
    PolylineDashMaterial,
    PolylineGlowMaterial,
    PolylineOutlineMaterial,
    SolidColorMaterial,
    StripeMaterial,
)
from cesiumkit.properties import (
    CallbackProperty,
    ConstantProperty,
    ReferenceProperty,
    SampledPositionProperty,
    SampledProperty,
    TimeIntervalCollectionProperty,
)

# Scene & Globe
from cesiumkit.scene import SceneConfig

# Terrain Providers
from cesiumkit.terrain import (
    CesiumTerrainProvider,
    EllipsoidTerrainProvider,
    IonTerrainProvider,
    TerrainProvider,
)

# Viewer — the main entry point
from cesiumkit.viewer import Viewer

# Make named colors accessible as Color.RED, etc.
for _name in dir(_color_module):
    _obj = getattr(_color_module, _name)
    if isinstance(_obj, Color) and _name.isupper():
        setattr(Color, _name, _obj)
del _name, _obj

__all__ = [
    "__version__",
    # Core
    "CesiumBase",
    "CesiumEnum",
    "JsCode",
    "generate_id",
    # Coordinates
    "Cartesian2",
    "Cartesian3",
    "Cartesian3FromDegrees",
    "Cartesian3FromRadians",
    "Cartesian3DegreesArray",
    "Cartesian3DegreesArrayHeights",
    "Cartographic",
    "CartographicFromDegrees",
    "BoundingSphere",
    "RectangleCoords",
    "RectangleCoordsFromDegrees",
    "NearFarScalar",
    "DistanceDisplayCondition",
    # Math
    "HeadingPitchRoll",
    "HeadingPitchRollFromDegrees",
    "HeadingPitchRange",
    "Quaternion",
    "Matrix3",
    "Matrix4",
    # Color
    "Color",
    # Enums
    "HeightReference",
    "HorizontalOrigin",
    "VerticalOrigin",
    "LabelStyle",
    "ClassificationType",
    "SceneMode",
    "ShadowMode",
    "ColorBlendMode",
    "ArcType",
    "CornerType",
    "ClockRange",
    "ClockStep",
    "ScreenSpaceEventType",
    "StripeOrientation",
    # Materials
    "MaterialBase",
    "SolidColorMaterial",
    "ImageMaterial",
    "GridMaterial",
    "StripeMaterial",
    "CheckerboardMaterial",
    "PolylineGlowMaterial",
    "PolylineArrowMaterial",
    "PolylineDashMaterial",
    "PolylineOutlineMaterial",
    # Entities
    "Entity",
    "EntityGraphics",
    "EntityCollection",
    "BillboardGraphics",
    "BoxGraphics",
    "CorridorGraphics",
    "CylinderGraphics",
    "EllipseGraphics",
    "EllipsoidGraphics",
    "LabelGraphics",
    "ModelGraphics",
    "PathGraphics",
    "PointGraphics",
    "PolygonGraphics",
    "PolygonHierarchy",
    "PolylineGraphics",
    "PolylineVolumeGraphics",
    "RectangleGraphics",
    "WallGraphics",
    "Cesium3DTilesetGraphics",
    # Time & Properties
    "JulianDate",
    "ClockConfig",
    "ConstantProperty",
    "SampledProperty",
    "SampledPositionProperty",
    "TimeIntervalCollectionProperty",
    "CallbackProperty",
    "ReferenceProperty",
    # Data Sources
    "CzmlDataSource",
    "GeoJsonDataSource",
    "KmlDataSource",
    "CustomDataSource",
    # Imagery
    "ImageryProvider",
    "IonImageryProvider",
    "BingMapsImageryProvider",
    "OpenStreetMapImageryProvider",
    "TileMapServiceImageryProvider",
    "UrlTemplateImageryProvider",
    "WebMapServiceImageryProvider",
    "WebMapTileServiceImageryProvider",
    "SingleTileImageryProvider",
    # Terrain
    "TerrainProvider",
    "EllipsoidTerrainProvider",
    "CesiumTerrainProvider",
    "IonTerrainProvider",
    # Camera
    "Camera",
    "CameraPosition",
    "FlyToOptions",
    "LookAtOptions",
    # Scene & Globe
    "SceneConfig",
    "GlobeConfig",
    # Ion
    "Ion",
    "IonResource",
    "Cesium3DTileset",
    # Events
    "EventHandler",
    # CZML
    "CzmlDocument",
    # Viewer
    "Viewer",
]
