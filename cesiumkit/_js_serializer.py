"""JavaScript serialization utilities for converting Python values to JS literals."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from enum import Enum
from typing import Any, cast

_JS_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def camelize(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _js_escape(js_string: str) -> str:
    """Make a JSON literal safe to embed in an inline ``<script>`` element."""
    return (
        js_string.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _json_literal(value: Any) -> str:
    """Serialize a JSON-compatible value for use inside inline JavaScript."""
    return _js_escape(json.dumps(value))


def _to_js_mapping(mapping: Mapping[Any, Any]) -> str:
    """Build a JS object while preserving mapping keys exactly.

    Mapping values frequently represent payloads such as GeoJSON or CZML. Those
    keys are data, not Python option field names, so they must never be
    camel-cased. JSON strings are valid JavaScript property names and avoid
    identifier/key injection.
    """
    parts = [f"[{_json_literal(str(key))}]: {to_js_value(value)}" for key, value in mapping.items()]
    return "{\n    " + ",\n    ".join(parts) + "\n}" if parts else "{}"


def _option_key(name: str) -> str:
    """Return a safe JavaScript property key for a known option field."""
    camelized = camelize(name)
    if _JS_IDENTIFIER.fullmatch(camelized) and camelized != "__proto__":
        return camelized
    return f"[{_json_literal(camelized)}]"


def to_js_value(obj: Any) -> str:
    """Convert a Python value to its JavaScript literal representation.

    - None -> undefined (or omitted)
    - bool -> true/false
    - int/float -> numeric literal
    - str -> quoted string (escaped)
    - list/tuple -> JS array literal
    - CesiumBase subclass -> calls obj.to_js()
    - JsCode -> raw JS code insertion
    - Enum with to_js() -> calls to_js()
    """
    from cesiumkit.utils import JsCode

    if obj is None:
        return "undefined"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    # Enum MUST be checked before str, because CesiumEnum inherits from str
    if isinstance(obj, Enum):
        to_js = getattr(obj, "to_js", None)
        if callable(to_js):
            return cast(str, to_js())
        return _json_literal(obj.value)
    if isinstance(obj, (int, float)):
        if isinstance(obj, float) and not math.isfinite(obj):
            if math.isnan(obj):
                return "NaN"
            return "Infinity" if obj > 0 else "-Infinity"
        return repr(obj)
    if isinstance(obj, JsCode):
        return obj.js_code
    if hasattr(obj, "to_js"):
        return obj.to_js()
    if isinstance(obj, str):
        # Escape <, >, & so strings can never terminate an inline <script>
        # element even when they are interpolated into HTML pages.
        return _json_literal(obj)
    if isinstance(obj, (list, tuple)):
        items = ", ".join(to_js_value(item) for item in obj)
        return f"[{items}]"
    if isinstance(obj, Mapping):
        return _to_js_mapping(obj)
    return _json_literal(obj)


def to_js_options(fields: dict[str, Any], exclude_none: bool = True) -> str:
    """Build a JS object literal {key: value, ...} from a dict of Python values.

    Keys are camelCased automatically. This function is for known Cesium
    option-field names only; arbitrary data mappings should be passed to
    :func:`to_js_value`, which preserves their keys verbatim.
    """
    parts: list[str] = []
    for key, value in fields.items():
        if exclude_none and value is None:
            continue
        js_key = _option_key(key)
        js_val = to_js_value(value)
        parts.append(f"{js_key}: {js_val}")
    return "{\n    " + ",\n    ".join(parts) + "\n}" if parts else "{}"


def to_js_constructor(class_name: str, fields: dict[str, Any], exclude_none: bool = True) -> str:
    """Build a `new ClassName({...})` JS expression."""
    opts = to_js_options(fields, exclude_none)
    return f"new {class_name}({opts})"


def to_js_positional(class_name: str, *args: Any) -> str:
    """Build a `new ClassName(arg1, arg2, ...)` JS expression."""
    js_args = ", ".join(to_js_value(a) for a in args)
    return f"new {class_name}({js_args})"
