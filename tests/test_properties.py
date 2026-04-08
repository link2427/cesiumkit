"""Tests for cesiumkit.properties module."""

from cesiumkit.coordinates import Cartesian3
from cesiumkit.properties import (
    CallbackProperty,
    ConstantProperty,
    ReferenceProperty,
    SampledPositionProperty,
    SampledProperty,
    TimeIntervalCollectionProperty,
)
from cesiumkit.utils import JsCode


class TestConstantProperty:
    def test_to_js(self):
        p = ConstantProperty(value=42)
        assert p.to_js() == "42"

    def test_with_string(self):
        p = ConstantProperty(value="hello")
        assert p.to_js() == '"hello"'


class TestSampledProperty:
    def test_to_js(self):
        p = SampledProperty(value_type="Number")
        p.add_sample("2024-01-01T00:00:00Z", 0)
        p.add_sample("2024-01-01T06:00:00Z", 100)
        js = p.to_js()
        assert "SampledProperty" in js
        assert "addSample" in js
        assert "2024-01-01T00:00:00Z" in js


class TestSampledPositionProperty:
    def test_to_js(self):
        p = SampledPositionProperty()
        p.add_sample("2024-01-01T00:00:00Z", Cartesian3.from_degrees(-75, 35, 100000))
        p.add_sample("2024-01-01T06:00:00Z", Cartesian3.from_degrees(-125, 35, 100000))
        js = p.to_js()
        assert "SampledPositionProperty" in js
        assert "addSample" in js
        assert "fromDegrees" in js

    def test_czml_export(self):
        p = SampledPositionProperty()
        p.add_sample("2024-01-01T00:00:00Z", Cartesian3.from_degrees(-75, 35, 100000))
        czml = p.to_czml()
        assert "cartographicDegrees" in czml

    def test_add_samples(self):
        p = SampledPositionProperty()
        p.add_samples(
            ["2024-01-01T00:00:00Z", "2024-01-01T06:00:00Z"],
            [
                Cartesian3.from_degrees(-75, 35, 0),
                Cartesian3.from_degrees(-125, 35, 0),
            ],
        )
        js = p.to_js()
        assert js.count("addSample") == 2


class TestTimeIntervalCollectionProperty:
    def test_to_js(self):
        p = TimeIntervalCollectionProperty()
        p.add_interval("2024-01-01T00:00:00Z", "2024-01-01T06:00:00Z", 42)
        js = p.to_js()
        assert "TimeIntervalCollectionProperty" in js
        assert "TimeInterval" in js


class TestCallbackProperty:
    def test_to_js(self):
        p = CallbackProperty(
            callback=JsCode("function(time, result) { return 42; }"),
            is_constant=False,
        )
        js = p.to_js()
        assert "CallbackProperty" in js
        assert "function(time, result)" in js


class TestReferenceProperty:
    def test_to_js(self):
        p = ReferenceProperty(
            target_id="entity1",
            target_property_names=["position"],
        )
        js = p.to_js()
        assert "ReferenceProperty" in js
        assert "entity1" in js
