"""Tests for cesiumkit.utils module."""

from cesiumkit.utils import JsCode, generate_id


class TestJsCode:
    def test_construct_and_repr(self):
        code = JsCode("viewer.zoomTo(entity)")
        assert code.js_code == "viewer.zoomTo(entity)"
        assert repr(code) == "JsCode('viewer.zoomTo(entity)')"
        assert str(code) == "viewer.zoomTo(entity)"

    def test_equality(self):
        assert JsCode("a") == JsCode("a")
        assert JsCode("a") != JsCode("b")
        assert JsCode("a") != "a"  # not equal to a plain string
        assert JsCode("a") != 42

    def test_hash(self):
        assert hash(JsCode("a")) == hash(JsCode("a"))
        assert len({JsCode("a"), JsCode("a"), JsCode("b")}) == 2

    def test_usable_as_dict_key(self):
        d = {JsCode("x"): 1}
        assert d[JsCode("x")] == 1


class TestGenerateId:
    def test_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_str(self):
        assert isinstance(generate_id(), str)
