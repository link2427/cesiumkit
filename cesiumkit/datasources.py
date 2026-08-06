"""Data source types for loading external data into CesiumJS."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from cesiumkit._js_serializer import to_js_options, to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.entities._base import EntityCollection


class DataSource(CesiumBase):
    """Base for data sources."""

    name: str | None = None
    show: bool = True

    def _js_class_name(self) -> str:
        raise NotImplementedError

    def to_js(self) -> str:
        raise NotImplementedError

    def _apply_loaded_options(self, expression: str) -> str:
        """Apply common DataSource properties after an asynchronous load."""
        assignments: list[str] = []
        if self.name is not None:
            assignments.append(f"dataSource.name = {to_js_value(self.name)};")
        if not self.show:
            assignments.append("dataSource.show = false;")
        if not assignments:
            return expression
        return f"(async () => {{const dataSource = await {expression};{''.join(assignments)}return dataSource;}})()"


class CzmlDataSource(DataSource):
    """Load CZML data."""

    url: str | None = Field(default=None, min_length=1)
    data: list[dict[str, Any]] | None = None
    source_uri: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _exactly_one_source(self) -> CzmlDataSource:
        if (self.url is None) == (self.data is None):
            raise ValueError("exactly one of url or data must be provided")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.CzmlDataSource"

    def to_js(self) -> str:
        source = self.url if self.url is not None else self.data
        options = {"source_uri": self.source_uri} if self.source_uri is not None else {}
        suffix = f", {to_js_options(options)}" if options else ""
        return self._apply_loaded_options(f"Cesium.CzmlDataSource.load({to_js_value(source)}{suffix})")


class GeoJsonDataSource(DataSource):
    """Load GeoJSON data."""

    url: str | None = Field(default=None, min_length=1)
    data: dict | None = None
    source_uri: str | None = Field(default=None, min_length=1)
    clamp_to_ground: bool = False
    stroke: Any = None  # Color
    stroke_width: float | None = None
    fill: Any = None  # Color
    marker_size: float | None = None
    marker_symbol: str | None = None
    marker_color: Any = None  # Color

    @model_validator(mode="after")
    def _exactly_one_source(self) -> GeoJsonDataSource:
        if (self.url is None) == (self.data is None):
            raise ValueError("exactly one of url or data must be provided")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.GeoJsonDataSource"

    def to_js(self) -> str:
        source = to_js_value(self.url if self.url is not None else self.data)

        opts: dict[str, Any] = {}
        if self.source_uri is not None:
            opts["source_uri"] = self.source_uri
        if self.clamp_to_ground:
            opts["clamp_to_ground"] = True
        if self.stroke is not None:
            opts["stroke"] = self.stroke
        if self.stroke_width is not None:
            opts["stroke_width"] = self.stroke_width
        if self.fill is not None:
            opts["fill"] = self.fill
        if self.marker_size is not None:
            opts["marker_size"] = self.marker_size
        if self.marker_symbol is not None:
            opts["marker_symbol"] = self.marker_symbol
        if self.marker_color is not None:
            opts["marker_color"] = self.marker_color

        if opts:
            expression = f"Cesium.GeoJsonDataSource.load({source}, {to_js_options(opts)})"
        else:
            expression = f"Cesium.GeoJsonDataSource.load({source})"

        return self._apply_loaded_options(expression)


class KmlDataSource(DataSource):
    """Load KML/KMZ data."""

    url: str = Field(min_length=1)
    clamp_to_ground: bool = False
    source_uri: str | None = Field(default=None, min_length=1)

    def _js_class_name(self) -> str:
        return "Cesium.KmlDataSource"

    def to_js(self) -> str:
        source = to_js_value(self.url)
        options: dict[str, Any] = {}
        if self.clamp_to_ground:
            options["clamp_to_ground"] = True
        if self.source_uri is not None:
            options["source_uri"] = self.source_uri
        suffix = f", {to_js_options(options)}" if options else ""

        return self._apply_loaded_options(f"Cesium.KmlDataSource.load({source}{suffix})")


class CustomDataSource(DataSource):
    """A custom data source with manually managed entities."""

    entities: EntityCollection = Field(default_factory=EntityCollection)

    def _js_class_name(self) -> str:
        return "Cesium.CustomDataSource"

    def to_js(self) -> str:
        expression = (
            f"new Cesium.CustomDataSource({to_js_value(self.name)})"
            if self.name is not None
            else "new Cesium.CustomDataSource()"
        )
        if self.show:
            return expression
        return f"(() => {{const dataSource = {expression};dataSource.show = false;return dataSource;}})()"


__all__ = [
    "CustomDataSource",
    "CzmlDataSource",
    "DataSource",
    "GeoJsonDataSource",
    "KmlDataSource",
]
