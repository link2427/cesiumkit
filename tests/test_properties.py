"""Tests for cesiumkit.properties module."""

import pytest
from pydantic import ValidationError

from cesiumkit._deprecations import CesiumkitDeprecationWarning
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

    def test_cesium_value_type(self):
        assert "new Cesium.SampledProperty(Cesium.Cartesian3)" in SampledProperty(value_type="Cartesian3").to_js()

    def test_arbitrary_value_type_requires_js_code(self):
        with pytest.raises(ValidationError):
            SampledProperty(value_type="Number); alert(1)")
        prop = SampledProperty(value_type=JsCode("CustomPackable"))
        assert "new Cesium.SampledProperty(CustomPackable)" in prop.to_js()

    def test_sample_time_is_inline_script_safe(self):
        prop = SampledProperty()
        prop.add_sample('2024-01-01T00:00:00Z</script><script>alert("x")</script>', 1)
        assert "</script>" not in prop.to_js()

    def test_add_samples_rejects_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            SampledProperty().add_samples(["2024-01-01T00:00:00Z"], [1, 2])


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

    def test_add_samples_rejects_length_mismatch(self):
        with pytest.raises(ValueError, match="same length"):
            SampledPositionProperty().add_samples([], [Cartesian3(x=0, y=0, z=0)])

    def test_default_lagrange_interpolation_is_applied(self):
        assert "Cesium.LagrangePolynomialApproximation" in SampledPositionProperty().to_js()

    def test_radian_positions_export_as_radians(self):
        p = SampledPositionProperty()
        p.add_sample("2024-01-01T00:00:00Z", Cartesian3.from_radians(1.0, 0.5, 10))
        assert p.to_czml() == {"cartographicRadians": ["2024-01-01T00:00:00Z", 1.0, 0.5, 10.0]}

    def test_rejects_invalid_or_mixed_position_representations(self):
        p = SampledPositionProperty()
        with pytest.raises(TypeError, match="position"):
            p.add_sample("2024-01-01T00:00:00Z", object())
        p.add_sample("2024-01-01T00:00:00Z", Cartesian3.from_degrees(1, 2))
        with pytest.raises(ValueError, match="same coordinate"):
            p.add_sample("2024-01-02T00:00:00Z", Cartesian3(x=1, y=2, z=3))


class TestTimeIntervalCollectionProperty:
    def test_to_js(self):
        p = TimeIntervalCollectionProperty()
        p.add_interval("2024-01-01T00:00:00Z", "2024-01-01T06:00:00Z", 42)
        js = p.to_js()
        assert "TimeIntervalCollectionProperty" in js
        assert "TimeInterval" in js

    def test_interval_times_must_be_non_empty_strings(self):
        with pytest.raises(TypeError, match="start and stop"):
            TimeIntervalCollectionProperty().add_interval("", "2024-01-01T00:00:00Z", 42)


class TestCallbackProperty:
    def test_to_js(self):
        p = CallbackProperty(
            callback=JsCode("function(time, result) { return 42; }"),
            is_constant=False,
        )
        js = p.to_js()
        assert "CallbackProperty" in js
        assert "function(time, result)" in js

    def test_raw_callback_string_is_deprecated_but_compatible(self):
        with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
            prop = CallbackProperty(callback="function() { return 1; }")
        assert prop.to_js() == "new Cesium.CallbackProperty(function() { return 1; }, false)"

    def test_raw_callback_assignment_warns(self):
        prop = CallbackProperty(callback=JsCode("function() { return 0; }"))
        with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
            prop.callback = "function() { return 1; }"
        assert prop.to_js() == "new Cesium.CallbackProperty(function() { return 1; }, false)"


class TestReferenceProperty:
    def test_to_js(self):
        p = ReferenceProperty(
            target_id="entity1",
            target_property_names=["position"],
        )
        js = p.to_js()
        assert "ReferenceProperty" in js
        assert "entity1" in js

    def test_values_are_escaped(self):
        prop = ReferenceProperty(
            target_id='entity"</script>',
            target_property_names=['position"], alert(1), ["'],
        )
        assert "</script>" not in prop.to_js()
        assert "\\u003c/script\\u003e" in prop.to_js()

    def test_collection_requires_safe_identifier_or_js_code(self):
        with pytest.raises(ValidationError, match="target_collection"):
            ReferenceProperty(
                target_collection="viewer.entities); alert(1)",
                target_id="entity1",
                target_property_names=["position"],
            )
        prop = ReferenceProperty(
            target_collection=JsCode("getCollection()"),
            target_id="entity1",
            target_property_names=["position"],
        )
        assert "ReferenceProperty(getCollection()" in prop.to_js()
