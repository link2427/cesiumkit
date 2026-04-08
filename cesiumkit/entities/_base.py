"""Base entity classes for cesiumkit."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from cesiumkit.base import CesiumBase
from cesiumkit._js_serializer import camelize, to_js_value
from cesiumkit.utils import generate_id


class EntityGraphics(CesiumBase):
    """Base class for all entity graphics types (PointGraphics, PolygonGraphics, etc.).

    Subclasses define the specific properties for each graphics type.
    Serializes as a plain JS object literal (not a constructor call) because
    CesiumJS Entity.add() accepts plain option objects for graphics.
    """

    show: bool | None = None

    def _graphics_key(self) -> str:
        """Return the Entity property name for this graphics type, e.g. 'point'."""
        raise NotImplementedError

    def _js_class_name(self) -> str:
        return f"Cesium.{self.__class__.__name__}"

    def to_js(self) -> str:
        """Serialize as a JS object literal for use inside Entity options."""
        fields = self._js_fields()
        parts: list[str] = []
        for key, value in fields.items():
            js_key = camelize(key)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")
        if not parts:
            return "{}"
        return "{\n        " + ",\n        ".join(parts) + "\n    }"

    def to_czml(self) -> dict:
        """Serialize to a CZML-compatible dict."""
        fields = self._js_fields()
        result: dict[str, Any] = {}
        for key, value in fields.items():
            js_key = camelize(key)
            if hasattr(value, "to_czml"):
                result[js_key] = value.to_czml()
            elif isinstance(value, bool):
                result[js_key] = value
            elif isinstance(value, (int, float, str)):
                result[js_key] = value
            elif isinstance(value, (list, tuple)):
                result[js_key] = [
                    item.to_czml() if hasattr(item, "to_czml") else item
                    for item in value
                ]
        return result


# Graphics type field names on Entity (snake_case -> camelCase mapping)
_GRAPHICS_FIELDS = [
    "billboard",
    "box",
    "corridor",
    "cylinder",
    "ellipse",
    "ellipsoid",
    "label",
    "model",
    "path",
    "point",
    "polygon",
    "polyline",
    "polyline_volume",
    "rectangle",
    "wall",
    "tileset",
]


class Entity(CesiumBase):
    """A CesiumJS Entity with optional graphics attachments."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        arbitrary_types_allowed=True,
    )

    id: str | None = None
    name: str | None = None
    description: str | None = None
    show: bool = True
    position: Any = None
    orientation: Any = None
    availability: Any = None
    parent: Any = None

    # Graphics type fields
    billboard: Any = None
    box: Any = None
    corridor: Any = None
    cylinder: Any = None
    ellipse: Any = None
    ellipsoid: Any = None
    label: Any = None
    model: Any = None
    path: Any = None
    point: Any = None
    polygon: Any = None
    polyline: Any = None
    polyline_volume: Any = None
    rectangle: Any = None
    wall: Any = None
    tileset: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.Entity"

    def to_js(self) -> str:
        """Serialize to a JS object literal for use with viewer.entities.add()."""
        parts: list[str] = []

        # Core fields
        core_fields = ["id", "name", "description", "show", "position",
                        "orientation", "availability", "parent"]
        for field_name in core_fields:
            value = getattr(self, field_name)
            if value is None:
                continue
            # Skip show if it's the default True
            if field_name == "show" and value is True:
                continue
            js_key = camelize(field_name)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")

        # Graphics fields
        for field_name in _GRAPHICS_FIELDS:
            value = getattr(self, field_name)
            if value is None:
                continue
            js_key = camelize(field_name)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")

        if not parts:
            return "{}"
        return "{\n    " + ",\n    ".join(parts) + "\n}"

    def to_czml_packet(self) -> dict:
        """Build a CZML packet dict for this entity."""
        packet: dict[str, Any] = {}

        if self.id is not None:
            packet["id"] = self.id
        else:
            packet["id"] = generate_id()

        if self.name is not None:
            packet["name"] = self.name
        if self.description is not None:
            packet["description"] = self.description
        if not self.show:
            packet["show"] = False
        if self.availability is not None:
            packet["availability"] = self.availability

        if self.position is not None and hasattr(self.position, "to_czml"):
            packet["position"] = self.position.to_czml()

        if self.orientation is not None and hasattr(self.orientation, "to_czml"):
            packet["orientation"] = self.orientation.to_czml()

        # Graphics
        for field_name in _GRAPHICS_FIELDS:
            value = getattr(self, field_name)
            if value is None:
                continue
            js_key = camelize(field_name)
            if hasattr(value, "to_czml"):
                packet[js_key] = value.to_czml()

        return packet


class EntityCollection:
    """A collection of Entity objects, similar to CesiumJS EntityCollection."""

    def __init__(self) -> None:
        self._entities: list[Entity] = []

    def add(self, entity: Entity | None = None, **kwargs: Any) -> Entity:
        """Add an entity to the collection.

        Can pass an Entity instance or keyword arguments to construct one.
        """
        if entity is None:
            entity = Entity(**kwargs)
        self._entities.append(entity)
        return entity

    def remove(self, entity: Entity) -> bool:
        """Remove an entity from the collection. Returns True if found."""
        try:
            self._entities.remove(entity)
            return True
        except ValueError:
            return False

    def remove_all(self) -> None:
        """Remove all entities from the collection."""
        self._entities.clear()

    def get_by_id(self, id: str) -> Entity | None:
        """Find an entity by its id."""
        for entity in self._entities:
            if entity.id == id:
                return entity
        return None

    def __iter__(self):
        return iter(self._entities)

    def __len__(self) -> int:
        return len(self._entities)

    def __getitem__(self, index: int) -> Entity:
        return self._entities[index]
