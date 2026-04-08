"""Property system for time-dynamic values in cesiumkit."""

from __future__ import annotations

from typing import Any

from pydantic import Field, PrivateAttr

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

    value_type: str = "Number"
    interpolation_degree: int = 1
    interpolation_algorithm: str = "LINEAR"
    _samples: list[tuple[str, Any]] = PrivateAttr(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.SampledProperty"

    def add_sample(self, time: str | Any, value: Any) -> None:
        """Add a time-value sample.

        Args:
            time: ISO 8601 string or JulianDate
            value: The value at this time
        """
        if hasattr(time, "iso8601"):
            time = time.iso8601
        self._samples.append((time, value))

    def add_samples(self, times: list, values: list) -> None:
        """Add multiple samples at once."""
        for t, v in zip(times, values):
            self.add_sample(t, v)

    def to_js(self) -> str:
        lines = ["(function() {"]
        lines.append(f"    var prop = new Cesium.SampledProperty({self.value_type});")

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
            time_js = f'Cesium.JulianDate.fromIso8601("{time_str}")'
            val_js = to_js_value(value)
            lines.append(f"    prop.addSample({time_js}, {val_js});")

        lines.append("    return prop;")
        lines.append("})()")
        return "\n".join(lines)


class SampledPositionProperty(PropertyBase):
    """A SampledProperty specialized for Cartesian3 positions."""

    interpolation_degree: int = 1
    interpolation_algorithm: str = "LAGRANGE"
    _samples: list[tuple[str, Any]] = PrivateAttr(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.SampledPositionProperty"

    def add_sample(self, time: str | Any, position: Any) -> None:
        """Add a time-position sample.

        Args:
            time: ISO 8601 string or JulianDate
            position: Cartesian3 or Cartesian3FromDegrees
        """
        if hasattr(time, "iso8601"):
            time = time.iso8601
        self._samples.append((time, position))

    def add_samples(self, times: list, positions: list) -> None:
        """Add multiple samples at once."""
        for t, p in zip(times, positions):
            self.add_sample(t, p)

    def to_js(self) -> str:
        lines = ["(function() {"]
        lines.append("    var positionProperty = new Cesium.SampledPositionProperty();")

        if self.interpolation_algorithm == "LAGRANGE" and self.interpolation_degree > 1:
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
            time_js = f'Cesium.JulianDate.fromIso8601("{time_str}")'
            pos_js = to_js_value(position)
            lines.append(f"    positionProperty.addSample({time_js}, {pos_js});")

        lines.append("    return positionProperty;")
        lines.append("})()")
        return "\n".join(lines)

    def to_czml(self) -> dict:
        """Export as CZML position with time-tagged samples."""
        # Check if positions are in degrees
        if self._samples and hasattr(self._samples[0][1], "longitude"):
            values: list[Any] = []
            for time_str, pos in self._samples:
                values.extend([time_str, pos.longitude, pos.latitude, pos.height])
            return {"cartographicDegrees": values}
        else:
            values = []
            for time_str, pos in self._samples:
                if hasattr(pos, "x"):
                    values.extend([time_str, pos.x, pos.y, pos.z])
            return {"cartesian": values}


class TimeIntervalCollectionProperty(PropertyBase):
    """Property defined over time intervals."""

    intervals: list[dict] = Field(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.TimeIntervalCollectionProperty"

    def add_interval(self, start: str, stop: str, data: Any) -> None:
        """Add a time interval with associated data."""
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
                f'start: Cesium.JulianDate.fromIso8601("{start}"), '
                f'stop: Cesium.JulianDate.fromIso8601("{stop}"), '
                f"data: {data_js}}}));"
            )
        lines.append("    return prop;")
        lines.append("})()")
        return "\n".join(lines)


class CallbackProperty(PropertyBase):
    """Property defined by a JS callback function."""

    callback: Any  # JsCode
    is_constant: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.CallbackProperty"

    def to_js(self) -> str:
        cb = self.callback
        if isinstance(cb, JsCode):
            cb = cb.js_code
        is_const = "true" if self.is_constant else "false"
        return f"new Cesium.CallbackProperty({cb}, {is_const})"


class ReferenceProperty(PropertyBase):
    """Property that references another entity's property."""

    target_collection: str = "viewer.entities"
    target_id: str = ""
    target_property_names: list[str] = Field(default_factory=list)

    def _js_class_name(self) -> str:
        return "Cesium.ReferenceProperty"

    def to_js(self) -> str:
        props = ", ".join(f'"{p}"' for p in self.target_property_names)
        return f'new Cesium.ReferenceProperty({self.target_collection}, "{self.target_id}", [{props}])'
