"""JavaScript serialization utilities for converting Python values to JS literals."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any


def camelize(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


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
        if hasattr(obj, "to_js"):
            return obj.to_js()
        return json.dumps(obj.value)
    if isinstance(obj, (int, float)):
        return repr(obj)
    if isinstance(obj, JsCode):
        return obj.js_code
    if hasattr(obj, "to_js"):
        return obj.to_js()
    if isinstance(obj, str):
        return json.dumps(obj)
    if isinstance(obj, (list, tuple)):
        items = ", ".join(to_js_value(item) for item in obj)
        return f"[{items}]"
    if isinstance(obj, dict):
        return to_js_options(obj)
    return json.dumps(obj)


def to_js_options(fields: dict[str, Any], exclude_none: bool = True) -> str:
    """Build a JS object literal {key: value, ...} from a dict of Python values.

    Keys are camelCased automatically.
    """
    parts: list[str] = []
    for key, value in fields.items():
        if exclude_none and value is None:
            continue
        js_key = camelize(key)
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
