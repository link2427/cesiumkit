"""Property system for time-dynamic values in cesiumkit."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import Field, PrivateAttr, field_validator

from cesiumkit._deprecations import warn_deprecated
from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.utils import JsCode


class PropertyBase(CesiumBase):
    """Base for the Cesium Property system."""

    def _js_class_name(self) -> str:
        raise NotImplementedError


class ConstantProperty(PropertyBase):
    """Wraps a constant value as a property."""

    value: Any

    def _js_class_name(self) -> str:
        return "Cesium.ConstantProperty"

    def to_js(self) -> str:
        return to_js_value(self.value)

    def to_czml(self) -> Any:
        if hasattr(self.value, "to_czml"):
            return self.value.to_czml()
        return self.value


class SampledProperty(PropertyBase):
    """A property with time-tagged samples and interpolation."""

    value_type: Literal["Number", "Cartesian2", "Cartesian3", "Cartesian4", "Quaternion", "Color"] | JsCode = "Number"
    interpolation_degree: int = Field(default=1, ge=1, strict=True)
    interpolation_algorithm: Literal["LINEAR", "LAGRANGE", "HERMITE"] = "LINEAR"
    _samples: list[tuple[str, Any]] = PrivateAttr(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.SampledProperty"

    def add_sample(self, time: str | Any, value: Any) -> None:
        """Add a time-value sample.

        Args:
            time: ISO 8601 string or JulianDate
            value: The value at this time
        """
        iso = time if isinstance(time, str) else getattr(time, "iso8601", None)
        if not isinstance(iso, str) or not iso:
            raise TypeError("time must be an ISO-8601 string or JulianDate")
        self._samples.append((iso, value))

    def add_samples(self, times: list, values: list) -> None:
        """Add multiple samples at once."""
        if len(times) != len(values):
            raise ValueError("times and values must have the same length")
        for t, v in zip(times, values):
            self.add_sample(t, v)

    def to_js(self) -> str:
        lines = ["(function() {"]
        if isinstance(self.value_type, JsCode):
            value_type_js = self.value_type.js_code
        elif self.value_type == "Number":
            value_type_js = "Number"
        else:
            value_type_js = f"Cesium.{self.value_type}"
        lines.append(f"    var prop = new Cesium.SampledProperty({value_type_js});")

        if self.interpolation_algorithm == "LAGRANGE":
            lines.append(
                f"    prop.setInterpolationOptions({{interpolationDegree: {self.interpolation_degree}, "
                f"interpolationAlgorithm: Cesium.LagrangePolynomialApproximation}});"
            )
        elif self.interpolation_algorithm == "HERMITE":
            lines.append(
                f"    prop.setInterpolationOptions({{interpolationDegree: {self.interpolation_degree}, "
                f"interpolationAlgorithm: Cesium.HermitePolynomialApproximation}});"
            )

        for time_str, value in self._samples:
            time_js = f"Cesium.JulianDate.fromIso8601({to_js_value(time_str)})"
            val_js = to_js_value(value)
            lines.append(f"    prop.addSample({time_js}, {val_js});")

        lines.append("    return prop;")
        lines.append("})()")
        return "\n".join(lines)


class SampledPositionProperty(PropertyBase):
    """A SampledProperty specialized for Cartesian3 positions."""

    interpolation_degree: int = Field(default=1, ge=1, strict=True)
    interpolation_algorithm: Literal["LINEAR", "LAGRANGE", "HERMITE"] = "LAGRANGE"
    _samples: list[tuple[str, Any]] = PrivateAttr(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.SampledPositionProperty"

    def add_sample(self, time: str | Any, position: Any) -> None:
        """Add a time-position sample.

        Args:
            time: ISO 8601 string or JulianDate
            position: Cartesian3 or Cartesian3FromDegrees
        """
        iso = time if isinstance(time, str) else getattr(time, "iso8601", None)
        if not isinstance(iso, str) or not iso:
            raise TypeError("time must be an ISO-8601 string or JulianDate")
        encoding = self._position_encoding(position)
        if self._samples and self._position_encoding(self._samples[0][1]) != encoding:
            raise ValueError("all sampled positions must use the same coordinate representation")
        self._samples.append((iso, position))

    @staticmethod
    def _position_encoding(position: Any) -> str:
        from cesiumkit.coordinates import Cartesian3, Cartesian3FromDegrees, Cartesian3FromRadians

        if isinstance(position, Cartesian3FromDegrees):
            return "cartographicDegrees"
        if isinstance(position, Cartesian3FromRadians):
            return "cartographicRadians"
        if type(position) is Cartesian3:
            return "cartesian"
        raise TypeError("position must be a Cartesian3, Cartesian3FromDegrees, or Cartesian3FromRadians")

    def add_samples(self, times: list, positions: list) -> None:
        """Add multiple samples at once."""
        if len(times) != len(positions):
            raise ValueError("times and positions must have the same length")
        for t, p in zip(times, positions):
            self.add_sample(t, p)

    def to_js(self) -> str:
        lines = ["(function() {"]
        lines.append("    var positionProperty = new Cesium.SampledPositionProperty();")

        if self.interpolation_algorithm == "LAGRANGE":
            lines.append(
                f"    positionProperty.setInterpolationOptions({{"
                f"interpolationDegree: {self.interpolation_degree}, "
                f"interpolationAlgorithm: Cesium.LagrangePolynomialApproximation}});"
            )
        elif self.interpolation_algorithm == "HERMITE":
            lines.append(
                f"    positionProperty.setInterpolationOptions({{"
                f"interpolationDegree: {self.interpolation_degree}, "
                f"interpolationAlgorithm: Cesium.HermitePolynomialApproximation}});"
            )

        for time_str, position in self._samples:
            time_js = f"Cesium.JulianDate.fromIso8601({to_js_value(time_str)})"
            pos_js = to_js_value(position)
            lines.append(f"    positionProperty.addSample({time_js}, {pos_js});")

        lines.append("    return positionProperty;")
        lines.append("})()")
        return "\n".join(lines)

    def to_czml(self) -> dict:
        """Export as CZML position with time-tagged samples."""
        encoding = self._position_encoding(self._samples[0][1]) if self._samples else "cartesian"
        if encoding in {"cartographicDegrees", "cartographicRadians"}:
            values: list[Any] = []
            for time_str, pos in self._samples:
                values.extend([time_str, pos.longitude, pos.latitude, pos.height])
            return {encoding: values}
        else:
            values = []
            for time_str, pos in self._samples:
                values.extend([time_str, pos.x, pos.y, pos.z])
            return {"cartesian": values}


class TimeIntervalCollectionProperty(PropertyBase):
    """Property defined over time intervals."""

    intervals: list[dict] = Field(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.TimeIntervalCollectionProperty"

    def add_interval(self, start: str, stop: str, data: Any) -> None:
        """Add a time interval with associated data."""
        if not isinstance(start, str) or not start or not isinstance(stop, str) or not stop:
            raise TypeError("start and stop must be non-empty ISO-8601 strings")
        self.intervals.append({"start": start, "stop": stop, "data": data})

    def to_js(self) -> str:
        lines = ["(function() {"]
        lines.append("    var prop = new Cesium.TimeIntervalCollectionProperty();")
        for interval in self.intervals:
            start = interval["start"]
            stop = interval["stop"]
            data_js = to_js_value(interval["data"])
            lines.append(
                f"    prop.intervals.addInterval(new Cesium.TimeInterval({{"
                f"start: Cesium.JulianDate.fromIso8601({to_js_value(start)}), "
                f"stop: Cesium.JulianDate.fromIso8601({to_js_value(stop)}), "
                f"data: {data_js}}}));"
            )
        lines.append("    return prop;")
        lines.append("})()")
        return "\n".join(lines)


class CallbackProperty(PropertyBase):
    """Property defined by a JS callback function.

    Wrap callbacks in :class:`JsCode`. Raw strings remain accepted through
    1.x for compatibility with 0.x and emit a project deprecation warning.
    """

    callback: JsCode | str
    is_constant: bool = False

    @field_validator("callback")
    @classmethod
    def _warn_for_raw_callback(cls, value: JsCode | str) -> JsCode | str:
        if isinstance(value, str):
            warn_deprecated(
                "CallbackProperty(callback=<str>)",
                alternative="CallbackProperty(callback=JsCode(...))",
            )
        return value

    def _js_class_name(self) -> str:
        return "Cesium.CallbackProperty"

    def to_js(self) -> str:
        is_const = "true" if self.is_constant else "false"
        callback = self.callback.js_code if isinstance(self.callback, JsCode) else self.callback
        return f"new Cesium.CallbackProperty({callback}, {is_const})"


class ReferenceProperty(PropertyBase):
    """Property that references another entity's property."""

    target_collection: str | JsCode = "viewer.entities"
    target_id: str = Field(min_length=1)
    target_property_names: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1)

    @field_validator("target_collection")
    @classmethod
    def _collection_is_safe_expression(cls, value: str | JsCode) -> str | JsCode:
        dotted_identifier = r"[A-Za-z_$][A-Za-z0-9_$]*(\.[A-Za-z_$][A-Za-z0-9_$]*)*"
        if isinstance(value, str) and re.fullmatch(dotted_identifier, value) is None:
            raise ValueError("target_collection must be a dotted identifier or JsCode")
        return value

    def _js_class_name(self) -> str:
        return "Cesium.ReferenceProperty"

    def to_js(self) -> str:
        collection = (
            self.target_collection.js_code if isinstance(self.target_collection, JsCode) else self.target_collection
        )
        return (
            f"new Cesium.ReferenceProperty({collection}, {to_js_value(self.target_id)}, "
            f"{to_js_value(self.target_property_names)})"
        )


__all__ = [
    "CallbackProperty",
    "ConstantProperty",
    "PropertyBase",
    "ReferenceProperty",
    "SampledPositionProperty",
    "SampledProperty",
    "TimeIntervalCollectionProperty",
]
