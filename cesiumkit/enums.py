"""All CesiumJS enumerations."""

from __future__ import annotations

from cesiumkit.base import CesiumEnum


class HeightReference(CesiumEnum):
    NONE = "NONE"
    CLAMP_TO_GROUND = "CLAMP_TO_GROUND"
    RELATIVE_TO_GROUND = "RELATIVE_TO_GROUND"


class HorizontalOrigin(CesiumEnum):
    CENTER = "CENTER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class VerticalOrigin(CesiumEnum):
    CENTER = "CENTER"
    BOTTOM = "BOTTOM"
    TOP = "TOP"
    BASELINE = "BASELINE"


class LabelStyle(CesiumEnum):
    FILL = "FILL"
    OUTLINE = "OUTLINE"
    FILL_AND_OUTLINE = "FILL_AND_OUTLINE"


class ClassificationType(CesiumEnum):
    TERRAIN = "TERRAIN"
    CESIUM_3D_TILE = "CESIUM_3D_TILE"
    BOTH = "BOTH"


class SceneMode(CesiumEnum):
    MORPHING = "MORPHING"
    COLUMBUS_VIEW = "COLUMBUS_VIEW"
    SCENE2D = "SCENE2D"
    SCENE3D = "SCENE3D"


class ShadowMode(CesiumEnum):
    DISABLED = "DISABLED"
    ENABLED = "ENABLED"
    CAST_ONLY = "CAST_ONLY"
    RECEIVE_ONLY = "RECEIVE_ONLY"


class ColorBlendMode(CesiumEnum):
    HIGHLIGHT = "HIGHLIGHT"
    REPLACE = "REPLACE"
    MIX = "MIX"


class ArcType(CesiumEnum):
    NONE = "NONE"
    GEODESIC = "GEODESIC"
    RHUMB = "RHUMB"


class CornerType(CesiumEnum):
    ROUNDED = "ROUNDED"
    MITERED = "MITERED"
    BEVELED = "BEVELED"


class ClockRange(CesiumEnum):
    UNBOUNDED = "UNBOUNDED"
    CLAMPED = "CLAMPED"
    LOOP_STOP = "LOOP_STOP"


class ClockStep(CesiumEnum):
    TICK_DEPENDENT = "TICK_DEPENDENT"
    SYSTEM_CLOCK_MULTIPLIER = "SYSTEM_CLOCK_MULTIPLIER"
    SYSTEM_CLOCK = "SYSTEM_CLOCK"


class ScreenSpaceEventType(CesiumEnum):
    LEFT_CLICK = "LEFT_CLICK"
    LEFT_DOUBLE_CLICK = "LEFT_DOUBLE_CLICK"
    LEFT_DOWN = "LEFT_DOWN"
    LEFT_UP = "LEFT_UP"
    RIGHT_CLICK = "RIGHT_CLICK"
    RIGHT_DOUBLE_CLICK = "RIGHT_DOUBLE_CLICK"
    RIGHT_DOWN = "RIGHT_DOWN"
    RIGHT_UP = "RIGHT_UP"
    MIDDLE_CLICK = "MIDDLE_CLICK"
    MIDDLE_DOWN = "MIDDLE_DOWN"
    MIDDLE_UP = "MIDDLE_UP"
    MOUSE_MOVE = "MOUSE_MOVE"
    WHEEL = "WHEEL"
    PINCH_START = "PINCH_START"
    PINCH_MOVE = "PINCH_MOVE"
    PINCH_END = "PINCH_END"


class StripeOrientation(CesiumEnum):
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"
