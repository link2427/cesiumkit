"""Tests for cesiumkit.math module."""

import pytest
from pydantic import ValidationError

from cesiumkit.math import (
    HeadingPitchRange,
    HeadingPitchRoll,
    HeadingPitchRollFromDegrees,
    Matrix3,
    Matrix4,
    Quaternion,
)


class TestHeadingPitchRoll:
    def test_js_class_name(self):
        assert HeadingPitchRoll()._js_class_name() == "Cesium.HeadingPitchRoll"

    def test_to_js(self):
        m = HeadingPitchRoll(heading=0.1, pitch=0.2, roll=0.3)
        assert m.to_js() == "new Cesium.HeadingPitchRoll(0.1, 0.2, 0.3)"

    def test_defaults(self):
        assert HeadingPitchRoll().to_js() == "new Cesium.HeadingPitchRoll(0.0, 0.0, 0.0)"

    def test_from_degrees(self):
        m = HeadingPitchRoll.from_degrees(heading=90, pitch=45)
        assert isinstance(m, HeadingPitchRollFromDegrees)
        assert m.heading == 90
        assert m.pitch == 45
        assert m.roll == 0.0


class TestHeadingPitchRollFromDegrees:
    def test_js_class_name(self):
        m = HeadingPitchRollFromDegrees()
        assert m._js_class_name() == "Cesium.HeadingPitchRoll"

    def test_to_js(self):
        m = HeadingPitchRollFromDegrees(heading=90, pitch=45, roll=30)
        js = m.to_js()
        assert "Cesium.Math.toRadians(90.0)" in js
        assert "Cesium.Math.toRadians(45.0)" in js
        assert "Cesium.Math.toRadians(30.0)" in js


class TestHeadingPitchRange:
    def test_js_class_name(self):
        assert HeadingPitchRange()._js_class_name() == "Cesium.HeadingPitchRange"

    def test_to_js(self):
        m = HeadingPitchRange(heading=0.1, pitch=-0.5, range=250000.0)
        assert m.to_js() == "new Cesium.HeadingPitchRange(0.1, -0.5, 250000.0)"

    def test_defaults(self):
        assert HeadingPitchRange().to_js() == "new Cesium.HeadingPitchRange(0.0, 0.0, 0.0)"


class TestQuaternion:
    def test_js_class_name(self):
        q = Quaternion(x=0, y=0, z=0, w=1)
        assert q._js_class_name() == "Cesium.Quaternion"

    def test_to_js(self):
        q = Quaternion(x=0.1, y=0.2, z=0.3, w=0.9)
        assert q.to_js() == "new Cesium.Quaternion(0.1, 0.2, 0.3, 0.9)"

    def test_to_czml(self):
        q = Quaternion(x=0, y=0, z=0, w=1)
        assert q.to_czml() == {"unitQuaternion": [0, 0, 0, 1]}


class TestMatrix3:
    def test_js_class_name(self):
        m = Matrix3(values=[1, 0, 0, 0, 1, 0, 0, 0, 1])
        assert m._js_class_name() == "Cesium.Matrix3"

    def test_to_js(self):
        m = Matrix3(values=[1, 0, 0, 0, 1, 0, 0, 0, 1])
        assert m.to_js() == "new Cesium.Matrix3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)"

    def test_requires_exactly_nine_finite_values(self):
        for values in ([1.0] * 8, [1.0] * 10, [1.0] * 8 + [float("nan")]):
            with pytest.raises(ValidationError):
                Matrix3(values=values)


class TestMatrix4:
    def test_js_class_name(self):
        m = Matrix4(values=[1.0] * 16)
        assert m._js_class_name() == "Cesium.Matrix4"

    def test_to_js(self):
        m = Matrix4(values=[1.0, 0.0, 0.0, 0.0] * 4)
        js = m.to_js()
        assert js.startswith("new Cesium.Matrix4(")
        assert js.count(",") == 15

    def test_requires_exactly_sixteen_finite_values(self):
        for values in ([1.0] * 15, [1.0] * 17, [1.0] * 15 + [float("inf")]):
            with pytest.raises(ValidationError):
                Matrix4(values=values)


def test_math_values_must_be_finite():
    with pytest.raises(ValidationError):
        HeadingPitchRoll(heading=float("nan"))
    with pytest.raises(ValidationError):
        Quaternion(x=0, y=0, z=0, w=float("inf"))


def test_heading_pitch_range_rejects_negative_range():
    with pytest.raises(ValidationError):
        HeadingPitchRange(range=-1)
