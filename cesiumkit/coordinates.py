"""Coordinate and spatial types for cesiumkit."""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from cesiumkit.base import CesiumBase

_FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class Cartesian2(CesiumBase):
    """A 2D Cartesian point."""

    x: _FiniteFloat
    y: _FiniteFloat

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian2"

    def to_js(self) -> str:
        return f"new Cesium.Cartesian2({self.x}, {self.y})"

    def to_czml(self) -> dict:
        return {"cartesian2": [self.x, self.y]}


class Cartesian3(CesiumBase):
    """A 3D Cartesian point in Earth-Centered, Earth-Fixed (ECEF) coordinates."""

    x: _FiniteFloat
    y: _FiniteFloat
    z: _FiniteFloat

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        return f"new Cesium.Cartesian3({self.x}, {self.y}, {self.z})"

    def to_czml(self) -> dict:
        return {"cartesian": [self.x, self.y, self.z]}

    @classmethod
    def from_degrees(cls, longitude: float, latitude: float, height: float = 0.0) -> Cartesian3FromDegrees:
        """Create a Cartesian3 from longitude/latitude in degrees."""
        return Cartesian3FromDegrees(
            longitude=longitude,
            latitude=latitude,
            height=height,
            x=0.0,
            y=0.0,
            z=0.0,
        )

    @classmethod
    def from_radians(cls, longitude: float, latitude: float, height: float = 0.0) -> Cartesian3FromRadians:
        """Create a Cartesian3 from longitude/latitude in radians."""
        return Cartesian3FromRadians(
            longitude=longitude,
            latitude=latitude,
            height=height,
            x=0.0,
            y=0.0,
            z=0.0,
        )

    @classmethod
    def from_degrees_array(cls, coordinates: list[float]) -> Cartesian3DegreesArray:
        """Create an array of Cartesian3 from a flat list [lon, lat, lon, lat, ...]."""
        return Cartesian3DegreesArray(coordinates=coordinates)

    @classmethod
    def from_degrees_array_heights(cls, coordinates: list[float]) -> Cartesian3DegreesArrayHeights:
        """Create an array from [lon, lat, h, lon, lat, h, ...]."""
        return Cartesian3DegreesArrayHeights(coordinates=coordinates)

    @classmethod
    def from_shapely(cls, geom: object) -> Cartesian3FromDegrees:
        """Create a Cartesian3 from a shapely Point (WGS84 lon/lat).

        Requires the geometry to be a Point; raises ValueError otherwise.
        Uses the Point's z coordinate as height if present, else 0.
        """
        from cesiumkit._shapely import is_shapely_geom, shapely_point_to_cartesian3

        if not is_shapely_geom(geom):
            raise ValueError(f"Expected a shapely geometry, got {type(geom).__name__}")
        if getattr(geom, "geom_type", None) != "Point":
            raise ValueError(
                f"Cartesian3.from_shapely only supports Point geometries, got {getattr(geom, 'geom_type', None)}"
            )
        return shapely_point_to_cartesian3(geom)


class Cartesian3FromDegrees(Cartesian3):
    """A Cartesian3 created from degrees. Serializes to Cesium.Cartesian3.fromDegrees()."""

    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    height: _FiniteFloat = 0.0
    x: _FiniteFloat = 0.0
    y: _FiniteFloat = 0.0
    z: _FiniteFloat = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        if self.height != 0.0:
            return f"Cesium.Cartesian3.fromDegrees({self.longitude}, {self.latitude}, {self.height})"
        return f"Cesium.Cartesian3.fromDegrees({self.longitude}, {self.latitude})"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": [self.longitude, self.latitude, self.height]}


class Cartesian3FromRadians(Cartesian3):
    """A Cartesian3 created from radians. Serializes to Cesium.Cartesian3.fromRadians()."""

    longitude: float = Field(ge=-math.pi, le=math.pi, allow_inf_nan=False)
    latitude: float = Field(ge=-math.pi / 2, le=math.pi / 2, allow_inf_nan=False)
    height: _FiniteFloat = 0.0
    x: _FiniteFloat = 0.0
    y: _FiniteFloat = 0.0
    z: _FiniteFloat = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        if self.height != 0.0:
            return f"Cesium.Cartesian3.fromRadians({self.longitude}, {self.latitude}, {self.height})"
        return f"Cesium.Cartesian3.fromRadians({self.longitude}, {self.latitude})"

    def to_czml(self) -> dict:
        return {"cartographicRadians": [self.longitude, self.latitude, self.height]}


class Cartesian3DegreesArray(CesiumBase):
    """An array of Cartesian3 from a flat degrees list. Used for polyline positions, etc."""

    coordinates: list[_FiniteFloat]

    @field_validator("coordinates")
    @classmethod
    def _validate_coordinate_pairs(cls, values: list[float]) -> list[float]:
        if len(values) < 2 or len(values) % 2:
            raise ValueError("coordinates must contain complete longitude/latitude pairs")
        for longitude, latitude in zip(values[0::2], values[1::2]):
            if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                raise ValueError("longitude/latitude values must be within [-180, 180] and [-90, 90]")
        return values

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        coords_str = ", ".join(str(c) for c in self.coordinates)
        return f"Cesium.Cartesian3.fromDegreesArray([{coords_str}])"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": self.coordinates}


class Cartesian3DegreesArrayHeights(CesiumBase):
    """An array of Cartesian3 from a flat [lon, lat, h, ...] list."""

    coordinates: list[_FiniteFloat]

    @field_validator("coordinates")
    @classmethod
    def _validate_coordinate_triples(cls, values: list[float]) -> list[float]:
        if len(values) < 3 or len(values) % 3:
            raise ValueError("coordinates must contain complete longitude/latitude/height triples")
        for longitude, latitude in zip(values[0::3], values[1::3]):
            if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                raise ValueError("longitude/latitude values must be within [-180, 180] and [-90, 90]")
        return values

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        coords_str = ", ".join(str(c) for c in self.coordinates)
        return f"Cesium.Cartesian3.fromDegreesArrayHeights([{coords_str}])"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": self.coordinates}


class Cartographic(CesiumBase):
    """A position defined by longitude, latitude (in radians), and height (in meters)."""

    longitude: float = Field(ge=-math.pi, le=math.pi, allow_inf_nan=False)
    latitude: float = Field(ge=-math.pi / 2, le=math.pi / 2, allow_inf_nan=False)
    height: _FiniteFloat = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartographic"

    def to_js(self) -> str:
        return f"new Cesium.Cartographic({self.longitude}, {self.latitude}, {self.height})"

    @classmethod
    def from_degrees(cls, longitude: float, latitude: float, height: float = 0.0) -> CartographicFromDegrees:
        """Create a Cartographic from degrees."""
        return CartographicFromDegrees(longitude=longitude, latitude=latitude, height=height)

    def to_czml(self) -> dict:
        return {"cartographicRadians": [self.longitude, self.latitude, self.height]}


class CartographicFromDegrees(Cartographic):
    """A Cartographic created from degrees."""

    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    height: _FiniteFloat = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartographic"

    def to_js(self) -> str:
        return f"Cesium.Cartographic.fromDegrees({self.longitude}, {self.latitude}, {self.height})"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": [self.longitude, self.latitude, self.height]}


class BoundingSphere(CesiumBase):
    """A bounding sphere with a center and radius."""

    center: Cartesian3
    radius: float = Field(ge=0, allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "Cesium.BoundingSphere"

    def to_js(self) -> str:
        return f"new Cesium.BoundingSphere({self.center.to_js()}, {self.radius})"


class RectangleCoords(CesiumBase):
    """A cartographic rectangle defined by west, south, east, north bounds (in radians)."""

    west: float = Field(ge=-math.pi, le=math.pi, allow_inf_nan=False)
    south: float = Field(ge=-math.pi / 2, le=math.pi / 2, allow_inf_nan=False)
    east: float = Field(ge=-math.pi, le=math.pi, allow_inf_nan=False)
    north: float = Field(ge=-math.pi / 2, le=math.pi / 2, allow_inf_nan=False)

    @model_validator(mode="after")
    def _latitude_bounds_are_ordered(self) -> RectangleCoords:
        if self.south > self.north:
            raise ValueError("south must be less than or equal to north")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.Rectangle"

    def to_js(self) -> str:
        return f"new Cesium.Rectangle({self.west}, {self.south}, {self.east}, {self.north})"

    @classmethod
    def from_degrees(cls, west: float, south: float, east: float, north: float) -> RectangleCoordsFromDegrees:
        """Create a Rectangle from bounds in degrees."""
        return RectangleCoordsFromDegrees(west=west, south=south, east=east, north=north)

    def to_czml(self) -> dict:
        return {"wsenRadians": [self.west, self.south, self.east, self.north]}


class RectangleCoordsFromDegrees(RectangleCoords):
    """A Rectangle created from degree bounds."""

    west: float = Field(ge=-180, le=180, allow_inf_nan=False)
    south: float = Field(ge=-90, le=90, allow_inf_nan=False)
    east: float = Field(ge=-180, le=180, allow_inf_nan=False)
    north: float = Field(ge=-90, le=90, allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "Cesium.Rectangle"

    def to_js(self) -> str:
        return f"Cesium.Rectangle.fromDegrees({self.west}, {self.south}, {self.east}, {self.north})"

    def to_czml(self) -> dict:
        return {"wsenDegrees": [self.west, self.south, self.east, self.north]}


class NearFarScalar(CesiumBase):
    """Scalar values at near and far camera distances."""

    near: float = Field(ge=0, allow_inf_nan=False)
    near_value: _FiniteFloat
    far: float = Field(gt=0, allow_inf_nan=False)
    far_value: _FiniteFloat

    @model_validator(mode="after")
    def _distances_are_ordered(self) -> NearFarScalar:
        if self.far <= self.near:
            raise ValueError("far must be greater than near")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.NearFarScalar"

    def to_js(self) -> str:
        return f"new Cesium.NearFarScalar({self.near}, {self.near_value}, {self.far}, {self.far_value})"

    def to_czml(self) -> dict:
        return {"nearFarScalar": [self.near, self.near_value, self.far, self.far_value]}


class DistanceDisplayCondition(CesiumBase):
    """Display condition based on camera distance."""

    near: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    far: float = float("inf")

    @model_validator(mode="after")
    def _distances_are_ordered(self) -> DistanceDisplayCondition:
        if math.isnan(self.far) or self.far <= self.near:
            raise ValueError("far must be greater than near")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.DistanceDisplayCondition"

    def to_js(self) -> str:
        return f"new Cesium.DistanceDisplayCondition({self.near}, {self.far})"

    def to_czml(self) -> dict:
        return {"distanceDisplayCondition": {"nearDistance": self.near, "farDistance": self.far}}


__all__ = [
    "BoundingSphere",
    "Cartesian2",
    "Cartesian3",
    "Cartesian3DegreesArray",
    "Cartesian3DegreesArrayHeights",
    "Cartesian3FromDegrees",
    "Cartesian3FromRadians",
    "Cartographic",
    "CartographicFromDegrees",
    "DistanceDisplayCondition",
    "NearFarScalar",
    "RectangleCoords",
    "RectangleCoordsFromDegrees",
]
