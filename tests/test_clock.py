"""Tests for clock and Julian date configuration."""

import datetime as dt

import pytest
from pydantic import ValidationError

from cesiumkit.clock import ClockConfig, JulianDate


def test_julian_date_serialization_is_inline_script_safe():
    value = JulianDate.from_iso8601('2026-01-01T00:00:00Z</script><script>alert("x")</script>')
    assert "</script>" not in value.to_js()
    assert "\\u003c/script\\u003e" in value.to_js()


def test_julian_date_requires_a_value():
    with pytest.raises(ValidationError):
        JulianDate()


def test_from_datetime_normalizes_to_utc():
    value = JulianDate.from_datetime(dt.datetime(2026, 1, 1, 1, 0, tzinfo=dt.timezone(dt.timedelta(hours=1))))
    assert value.iso8601 == "2026-01-01T00:00:00Z"


@pytest.mark.parametrize("multiplier", [float("nan"), float("inf")])
def test_clock_multiplier_must_be_finite(multiplier):
    with pytest.raises(ValidationError):
        ClockConfig(multiplier=multiplier)
