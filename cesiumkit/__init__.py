"""cesiumkit: Object-oriented Python interface for CesiumJS 3D geospatial visualization."""

from cesiumkit._version import __version__

# Core
from cesiumkit.base import CesiumBase, CesiumEnum
from cesiumkit.utils import JsCode, generate_id

# Coordinates & Math
from cesiumkit.coordinates import (
    Cartesian2,
    Cartesian3,
    Cartesian3FromDegrees,
    Cartesian3FromRadians,
    Cartesian3DegreesArray,
    Cartesian3DegreesArrayHeights,
    Cartographic,
    CartographicFromDegrees,
    BoundingSphere,
    RectangleCoords,
    RectangleCoordsFromDegrees,
    NearFarScalar,
    DistanceDisplayCondition,
)
from cesiumkit.math import (
    HeadingPitchRoll,
    HeadingPitchRollFromDegrees,
    HeadingPitchRange,
    Quaternion,
    Matrix3,
    Matrix4,
)

# Color
from cesiumkit.color import Color
from cesiumkit import color as _color_module
# Make named colors accessible as Color.RED, etc.
for _name in dir(_color_module):
    _obj = getattr(_color_module, _name)
    if isinstance(_obj, Color) and _name.isupper():
        setattr(Color, _name, _obj)
del _name, _obj

# Enums
from cesiumkit.enums import (
    HeightReference,
    HorizontalOrigin,
    VerticalOrigin,
    LabelStyle,
    ClassificationType,
    SceneMode,
    ShadowMode,
    ColorBlendMode,
    ArcType,
    CornerType,
    ClockRange,
    ClockStep,
    ScreenSpaceEventType,
    StripeOrientation,
)

# Materials
from cesiumkit.material import (
    MaterialBase,
    SolidColorMaterial,
    ImageMaterial,
    GridMaterial,
    StripeMaterial,
    CheckerboardMaterial,
    PolylineGlowMaterial,
    PolylineArrowMaterial,
    PolylineDashMaterial,
    PolylineOutlineMaterial,
)

# Entities
from cesiumkit.entities._base import Entity, EntityGraphics, EntityCollection
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
from cesiumkit.entities.wall import WallGraphics
from cesiumkit.entities.tileset import Cesium3DTilesetGraphics

# Time & Properties
from cesiumkit.clock import JulianDate, ClockConfig
from cesiumkit.properties import (
    ConstantProperty,
    SampledProperty,
    SampledPositionProperty,
    TimeIntervalCollectionProperty,
    CallbackProperty,
    ReferenceProperty,
)

# Data Sources
from cesiumkit.datasources import (
    CzmlDataSource,
    GeoJsonDataSource,
    KmlDataSource,
    CustomDataSource,
)

# Imagery Providers
from cesiumkit.imagery import (
    ImageryProvider,
    IonImageryProvider,
    BingMapsImageryProvider,
    OpenStreetMapImageryProvider,
    TileMapServiceImageryProvider,
    UrlTemplateImageryProvider,
    WebMapServiceImageryProvider,
    WebMapTileServiceImageryProvider,
    SingleTileImageryProvider,
)

# Terrain Providers
from cesiumkit.terrain import (
    TerrainProvider,
    EllipsoidTerrainProvider,
    CesiumTerrainProvider,
    IonTerrainProvider,
)

# Camera
from cesiumkit.camera import Camera, CameraPosition, FlyToOptions, LookAtOptions

# Scene & Globe
from cesiumkit.scene import SceneConfig
from cesiumkit.globe import GlobeConfig

# Ion
from cesiumkit.ion import Ion, IonResource, Cesium3DTileset

# Events
from cesiumkit.events import EventHandler

# CZML
from cesiumkit.czml import CzmlDocument

# Viewer — the main entry point
from cesiumkit.viewer import Viewer

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
