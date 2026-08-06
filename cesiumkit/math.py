"""Math types for cesiumkit: rotations, quaternions, and related structures."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from cesiumkit.base import CesiumBase

_FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class HeadingPitchRoll(CesiumBase):
    """Rotation defined by heading, pitch, and roll in radians."""

    heading: _FiniteFloat = 0.0
    pitch: _FiniteFloat = 0.0
    roll: _FiniteFloat = 0.0

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

    heading: _FiniteFloat = 0.0
    pitch: _FiniteFloat = 0.0
    roll: _FiniteFloat = 0.0

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

    heading: _FiniteFloat = 0.0
    pitch: _FiniteFloat = 0.0
    range: float = Field(default=0.0, ge=0, allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "Cesium.HeadingPitchRange"

    def to_js(self) -> str:
        return f"new Cesium.HeadingPitchRange({self.heading}, {self.pitch}, {self.range})"


class Quaternion(CesiumBase):
    """A rotation represented as a quaternion."""

    x: _FiniteFloat
    y: _FiniteFloat
    z: _FiniteFloat
    w: _FiniteFloat

    def _js_class_name(self) -> str:
        return "Cesium.Quaternion"

    def to_js(self) -> str:
        return f"new Cesium.Quaternion({self.x}, {self.y}, {self.z}, {self.w})"

    def to_czml(self) -> dict:
        return {"unitQuaternion": [self.x, self.y, self.z, self.w]}


class Matrix3(CesiumBase):
    """A 3x3 matrix stored as 9 values in column-major order."""

    values: list[_FiniteFloat] = Field(min_length=9, max_length=9)

    def _js_class_name(self) -> str:
        return "Cesium.Matrix3"

    def to_js(self) -> str:
        vals = ", ".join(str(v) for v in self.values)
        return f"new Cesium.Matrix3({vals})"


class Matrix4(CesiumBase):
    """A 4x4 matrix stored as 16 values in column-major order."""

    values: list[_FiniteFloat] = Field(min_length=16, max_length=16)

    def _js_class_name(self) -> str:
        return "Cesium.Matrix4"

    def to_js(self) -> str:
        vals = ", ".join(str(v) for v in self.values)
        return f"new Cesium.Matrix4({vals})"


__all__ = [
    "HeadingPitchRange",
    "HeadingPitchRoll",
    "HeadingPitchRollFromDegrees",
    "Matrix3",
    "Matrix4",
    "Quaternion",
]
