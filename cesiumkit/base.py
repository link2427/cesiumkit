"""Base classes for all cesiumkit models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from cesiumkit._js_serializer import camelize, to_js_value


class CesiumBase(BaseModel):
    """Root base class for all cesiumkit Pydantic models.

    Every subclass knows how to serialize itself to a JavaScript expression
    string via to_js(), and optionally to a CZML dict via to_czml().
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        arbitrary_types_allowed=True,
    )

    def _js_class_name(self) -> str:
        """Return the Cesium JS constructor name, e.g. 'Cesium.Color'."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement _js_class_name()")

    def _js_fields(self) -> dict[str, Any]:
        """Return the fields to include in JS serialization.

        By default, returns all non-None fields.
        """
        result = {}
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        return result

    def to_js(self) -> str:
        """Serialize to a JavaScript expression string.

        Default implementation: new Cesium.ClassName({camelCaseKey: value, ...})
        """
        fields = self._js_fields()
        if not fields:
            return f"new {self._js_class_name()}()"

        parts: list[str] = []
        for key, value in fields.items():
            js_key = camelize(key)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")

        opts = "{\n    " + ",\n    ".join(parts) + "\n}"
        return f"new {self._js_class_name()}({opts})"

    def to_czml(self) -> dict:
        """Serialize to a CZML-compatible dict. Override in subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support CZML export")


class CesiumEnum(str, Enum):
    """Base for all Cesium enumerations. Serializes to Cesium.EnumType.VALUE in JS."""

    def to_js(self) -> str:
        return f"Cesium.{self.__class__.__name__}.{self.value}"
