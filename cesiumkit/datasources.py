"""Data source types for loading external data into CesiumJS."""

from __future__ import annotations

import json
from typing import Any

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase


class DataSource(CesiumBase):
    """Base for data sources."""

    name: str | None = None
    show: bool = True

    def _js_class_name(self) -> str:
        raise NotImplementedError

    def to_js(self) -> str:
        raise NotImplementedError


class CzmlDataSource(DataSource):
    """Load CZML data."""

    url: str | None = None
    data: list[dict] | None = None
    source_uri: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.CzmlDataSource"

    def to_js(self) -> str:
        if self.url:
            return f'Cesium.CzmlDataSource.load("{self.url}")'
        elif self.data:
            return f"Cesium.CzmlDataSource.load({json.dumps(self.data)})"
        raise ValueError("CzmlDataSource requires url or data")


class GeoJsonDataSource(DataSource):
    """Load GeoJSON data."""

    url: str | None = None
    data: dict | None = None
    source_uri: str | None = None
    clamp_to_ground: bool = False
    stroke: Any = None  # Color
    stroke_width: float | None = None
    fill: Any = None  # Color
    marker_size: float | None = None
    marker_symbol: str | None = None
    marker_color: Any = None  # Color

    def _js_class_name(self) -> str:
        return "Cesium.GeoJsonDataSource"

    def to_js(self) -> str:
        source = None
        if self.url:
            source = f'"{self.url}"'
        elif self.data:
            source = json.dumps(self.data)
        else:
            raise ValueError("GeoJsonDataSource requires url or data")

        opts: dict[str, Any] = {}
        if self.clamp_to_ground:
            opts["clampToGround"] = True
        if self.stroke is not None:
            opts["stroke"] = self.stroke
        if self.stroke_width is not None:
            opts["strokeWidth"] = self.stroke_width
        if self.fill is not None:
            opts["fill"] = self.fill
        if self.marker_size is not None:
            opts["markerSize"] = self.marker_size
        if self.marker_symbol is not None:
            opts["markerSymbol"] = self.marker_symbol
        if self.marker_color is not None:
            opts["markerColor"] = self.marker_color

        if opts:
            # Build options manually since keys are already camelCase
            opt_parts = []
            for k, v in opts.items():
                if isinstance(v, bool):
                    opt_parts.append(f"{k}: {'true' if v else 'false'}")
                elif isinstance(v, (int, float)):
                    opt_parts.append(f"{k}: {v}")
                elif isinstance(v, str):
                    opt_parts.append(f'{k}: "{v}"')
                elif hasattr(v, "to_js"):
                    opt_parts.append(f"{k}: {v.to_js()}")
                else:
                    opt_parts.append(f"{k}: {to_js_value(v)}")
            opts_str = ", ".join(opt_parts)
            return f"Cesium.GeoJsonDataSource.load({source}, {{{opts_str}}})"

        return f"Cesium.GeoJsonDataSource.load({source})"


class KmlDataSource(DataSource):
    """Load KML/KMZ data."""

    url: str = ""
    clamp_to_ground: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.KmlDataSource"

    def to_js(self) -> str:
        opts: dict[str, Any] = {}
        if self.clamp_to_ground:
            opts["clampToGround"] = True

        if opts:
            opt_parts = [f"{k}: {'true' if v else 'false'}" for k, v in opts.items()]
            opts_str = ", ".join(opt_parts)
            return f'Cesium.KmlDataSource.load("{self.url}", {{{opts_str}}})'

        return f'Cesium.KmlDataSource.load("{self.url}")'


class CustomDataSource(DataSource):
    """A custom data source with manually managed entities."""

    def _js_class_name(self) -> str:
        return "Cesium.CustomDataSource"

    def to_js(self) -> str:
        if self.name:
            return f'new Cesium.CustomDataSource("{self.name}")'
        return "new Cesium.CustomDataSource()"
