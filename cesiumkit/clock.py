"""Clock and time types for cesiumkit."""

from __future__ import annotations

import datetime as dt
from typing import Any

from cesiumkit.base import CesiumBase
from cesiumkit.enums import ClockRange, ClockStep
from cesiumkit._js_serializer import to_js_value


class JulianDate(CesiumBase):
    """Wrapper for Cesium.JulianDate."""

    iso8601: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.JulianDate"

    def to_js(self) -> str:
        if self.iso8601:
            return f'Cesium.JulianDate.fromIso8601("{self.iso8601}")'
        raise ValueError("JulianDate requires iso8601 string")

    def to_czml(self) -> dict:
        return self.iso8601 or ""

    @classmethod
    def from_iso8601(cls, iso_string: str) -> JulianDate:
        """Create a JulianDate from an ISO 8601 string."""
        return cls(iso8601=iso_string)

    @classmethod
    def from_datetime(cls, datetime_obj: dt.datetime) -> JulianDate:
        """Create a JulianDate from a Python datetime."""
        return cls(iso8601=datetime_obj.isoformat() + "Z")

    @classmethod
    def now(cls) -> JulianDate:
        """Create a JulianDate for the current time."""
        return cls.from_datetime(dt.datetime.now(dt.timezone.utc))


class ClockConfig(CesiumBase):
    """Configuration for the Cesium clock/timeline."""

    start_time: JulianDate | None = None
    stop_time: JulianDate | None = None
    current_time: JulianDate | None = None
    clock_range: ClockRange | None = None
    clock_step: ClockStep | None = None
    multiplier: float | None = None
    should_animate: bool | None = None

    def _js_class_name(self) -> str:
        return "Cesium.Clock"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Generate JS statements to configure the clock after viewer creation."""
        stmts: list[str] = []
        if self.start_time is not None:
            stmts.append(f"{viewer_var}.clock.startTime = {self.start_time.to_js()};")
        if self.stop_time is not None:
            stmts.append(f"{viewer_var}.clock.stopTime = {self.stop_time.to_js()};")
        if self.current_time is not None:
            stmts.append(f"{viewer_var}.clock.currentTime = {self.current_time.to_js()};")
        if self.clock_range is not None:
            stmts.append(f"{viewer_var}.clock.clockRange = {self.clock_range.to_js()};")
        if self.clock_step is not None:
            stmts.append(f"{viewer_var}.clock.clockStep = {self.clock_step.to_js()};")
        if self.multiplier is not None:
            stmts.append(f"{viewer_var}.clock.multiplier = {self.multiplier};")
        if self.should_animate is not None:
            val = "true" if self.should_animate else "false"
            stmts.append(f"{viewer_var}.clock.shouldAnimate = {val};")
        return stmts

    def to_czml(self) -> dict:
        result: dict[str, Any] = {}
        if self.start_time and self.stop_time:
            result["interval"] = f"{self.start_time.iso8601}/{self.stop_time.iso8601}"
        if self.current_time:
            result["currentTime"] = self.current_time.iso8601
        if self.multiplier is not None:
            result["multiplier"] = self.multiplier
        if self.clock_range is not None:
            result["range"] = self.clock_range.value
        if self.clock_step is not None:
            result["step"] = self.clock_step.value
        return result
