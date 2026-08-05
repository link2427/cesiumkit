"""Tests for cesiumkit.base module."""

from cesiumkit._js_serializer import camelize, to_js_options, to_js_value


class TestCamelize:
    def test_single_word(self):
        assert camelize("name") == "name"

    def test_two_words(self):
        assert camelize("pixel_size") == "pixelSize"

    def test_three_words(self):
        assert camelize("height_reference") == "heightReference"

    def test_already_camel(self):
        assert camelize("pixelSize") == "pixelSize"


class TestToJsValue:
    def test_none(self):
        assert to_js_value(None) == "undefined"

    def test_bool_true(self):
        assert to_js_value(True) == "true"

    def test_bool_false(self):
        assert to_js_value(False) == "false"

    def test_int(self):
        assert to_js_value(42) == "42"

    def test_float(self):
        assert to_js_value(3.14) == "3.14"

    def test_string(self):
        assert to_js_value("hello") == '"hello"'

    def test_list(self):
        result = to_js_value([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_empty_list(self):
        assert to_js_value([]) == "[]"

    def test_string_escapes_script_tags(self):
        # a string containing </script> must never be able to terminate an
        # inline script element when interpolated into an HTML page
        result = to_js_value("</script><script>alert(1)</script>")
        assert "</script>" not in result
        assert "\\u003c/script\\u003e" in result

    def test_enum_value_escapes_script_tags(self):
        from enum import Enum

        class _WeirdValue(str, Enum):
            X = "</script>"

        result = to_js_value(_WeirdValue.X)
        assert "</script>" not in result
        assert "\\u003c/script\\u003e" in result


class TestToJsOptions:
    def test_simple(self):
        result = to_js_options({"pixel_size": 10, "color": "red"})
        assert "pixelSize: 10" in result
        assert 'color: "red"' in result

    def test_exclude_none(self):
        result = to_js_options({"name": "test", "value": None})
        assert "value" not in result
        assert "name" in result

    def test_empty(self):
        assert to_js_options({}) == "{}"
