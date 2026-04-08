"""Math types for cesiumkit: rotations, quaternions, and related structures."""

from __future__ import annotations

from cesiumkit.base import CesiumBase


class HeadingPitchRoll(CesiumBase):
    """Rotation defined by heading, pitch, and roll in radians."""

    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.HeadingPitchRoll"

    def to_js(self) -> str:
        return f"new Cesium.HeadingPitchRoll({self.heading}, {self.pitch}, {self.roll})"

    @classmethod
    def from_degrees(cls, heading: float = 0.0, pitch: float = 0.0, roll: float = 0.0) -> HeadingPitchRollFromDegrees:
        """Create from values in degrees."""
        return HeadingPitchRollFromDegrees(heading=heading, pitch=pitch, roll=roll)


class HeadingPitchRollFromDegrees(CesiumBase):
    """HeadingPitchRoll from degree values."""

    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.HeadingPitchRoll"

    def to_js(self) -> str:
        return (
            f"new Cesium.HeadingPitchRoll("
            f"Cesium.Math.toRadians({self.heading}), "
            f"Cesium.Math.toRadians({self.pitch}), "
            f"Cesium.Math.toRadians({self.roll}))"
        )


class HeadingPitchRange(CesiumBase):
    """Camera offset defined by heading, pitch, and range."""

    heading: float = 0.0
    pitch: float = 0.0
    range: float = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.HeadingPitchRange"

    def to_js(self) -> str:
        return f"new Cesium.HeadingPitchRange({self.heading}, {self.pitch}, {self.range})"


class Quaternion(CesiumBase):
    """A rotation represented as a quaternion."""

    x: float
    y: float
    z: float
    w: float

    def _js_class_name(self) -> str:
        return "Cesium.Quaternion"

    def to_js(self) -> str:
        return f"new Cesium.Quaternion({self.x}, {self.y}, {self.z}, {self.w})"

    def to_czml(self) -> dict:
        return {"unitQuaternion": [self.x, self.y, self.z, self.w]}


class Matrix3(CesiumBase):
    """A 3x3 matrix stored as 9 values in column-major order."""

    values: list[float]

    def _js_class_name(self) -> str:
        return "Cesium.Matrix3"

    def to_js(self) -> str:
        vals = ", ".join(str(v) for v in self.values)
        return f"new Cesium.Matrix3({vals})"


class Matrix4(CesiumBase):
    """A 4x4 matrix stored as 16 values in column-major order."""

    values: list[float]

    def _js_class_name(self) -> str:
        return "Cesium.Matrix4"

    def to_js(self) -> str:
        vals = ", ".join(str(v) for v in self.values)
        return f"new Cesium.Matrix4({vals})"
