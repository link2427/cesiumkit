"""Coordinate and spatial types for cesiumkit."""

from __future__ import annotations

from cesiumkit.base import CesiumBase


class Cartesian2(CesiumBase):
    """A 2D Cartesian point."""

    x: float
    y: float

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian2"

    def to_js(self) -> str:
        return f"new Cesium.Cartesian2({self.x}, {self.y})"

    def to_czml(self) -> dict:
        return {"cartesian2": [self.x, self.y]}


class Cartesian3(CesiumBase):
    """A 3D Cartesian point in Earth-Centered, Earth-Fixed (ECEF) coordinates."""

    x: float
    y: float
    z: float

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


class Cartesian3FromDegrees(CesiumBase):
    """A Cartesian3 created from degrees. Serializes to Cesium.Cartesian3.fromDegrees()."""

    longitude: float
    latitude: float
    height: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        if self.height != 0.0:
            return f"Cesium.Cartesian3.fromDegrees({self.longitude}, {self.latitude}, {self.height})"
        return f"Cesium.Cartesian3.fromDegrees({self.longitude}, {self.latitude})"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": [self.longitude, self.latitude, self.height]}


class Cartesian3FromRadians(CesiumBase):
    """A Cartesian3 created from radians. Serializes to Cesium.Cartesian3.fromRadians()."""

    longitude: float
    latitude: float
    height: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

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

    coordinates: list[float]

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        coords_str = ", ".join(str(c) for c in self.coordinates)
        return f"Cesium.Cartesian3.fromDegreesArray([{coords_str}])"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": self.coordinates}


class Cartesian3DegreesArrayHeights(CesiumBase):
    """An array of Cartesian3 from a flat [lon, lat, h, ...] list."""

    coordinates: list[float]

    def _js_class_name(self) -> str:
        return "Cesium.Cartesian3"

    def to_js(self) -> str:
        coords_str = ", ".join(str(c) for c in self.coordinates)
        return f"Cesium.Cartesian3.fromDegreesArrayHeights([{coords_str}])"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": self.coordinates}


class Cartographic(CesiumBase):
    """A position defined by longitude, latitude (in radians), and height (in meters)."""

    longitude: float
    latitude: float
    height: float = 0.0

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


class CartographicFromDegrees(CesiumBase):
    """A Cartographic created from degrees."""

    longitude: float
    latitude: float
    height: float = 0.0

    def _js_class_name(self) -> str:
        return "Cesium.Cartographic"

    def to_js(self) -> str:
        return f"Cesium.Cartographic.fromDegrees({self.longitude}, {self.latitude}, {self.height})"

    def to_czml(self) -> dict:
        return {"cartographicDegrees": [self.longitude, self.latitude, self.height]}


class BoundingSphere(CesiumBase):
    """A bounding sphere with a center and radius."""

    center: Cartesian3
    radius: float

    def _js_class_name(self) -> str:
        return "Cesium.BoundingSphere"

    def to_js(self) -> str:
        return f"new Cesium.BoundingSphere({self.center.to_js()}, {self.radius})"


class RectangleCoords(CesiumBase):
    """A cartographic rectangle defined by west, south, east, north bounds (in radians)."""

    west: float
    south: float
    east: float
    north: float

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


class RectangleCoordsFromDegrees(CesiumBase):
    """A Rectangle created from degree bounds."""

    west: float
    south: float
    east: float
    north: float

    def _js_class_name(self) -> str:
        return "Cesium.Rectangle"

    def to_js(self) -> str:
        return f"Cesium.Rectangle.fromDegrees({self.west}, {self.south}, {self.east}, {self.north})"

    def to_czml(self) -> dict:
        return {"wsenDegrees": [self.west, self.south, self.east, self.north]}


class NearFarScalar(CesiumBase):
    """Scalar values at near and far camera distances."""

    near: float
    near_value: float
    far: float
    far_value: float

    def _js_class_name(self) -> str:
        return "Cesium.NearFarScalar"

    def to_js(self) -> str:
        return f"new Cesium.NearFarScalar({self.near}, {self.near_value}, {self.far}, {self.far_value})"

    def to_czml(self) -> dict:
        return {"nearFarScalar": [self.near, self.near_value, self.far, self.far_value]}


class DistanceDisplayCondition(CesiumBase):
    """Display condition based on camera distance."""

    near: float = 0.0
    far: float = float("inf")

    def _js_class_name(self) -> str:
        return "Cesium.DistanceDisplayCondition"

    def to_js(self) -> str:
        return f"new Cesium.DistanceDisplayCondition({self.near}, {self.far})"

    def to_czml(self) -> dict:
        return {"distanceDisplayCondition": {"nearDistance": self.near, "farDistance": self.far}}
