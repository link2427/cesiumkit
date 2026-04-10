"""Shapely geometry conversion helpers.

Duck-typed so shapely is not a hard dependency. All helpers assume shapely
geometries use WGS84 lon/lat (EPSG:4326) since shapely is CRS-naive. Callers
that work with other coordinate systems (e.g. GeoPandas) should reproject
before calling these helpers.
"""

from __future__ import annotations

from typing import Any


def is_shapely_geom(obj: Any) -> bool:
    """Return True if obj looks like a shapely geometry (duck-typed).

    Checks for ``geom_type`` and ``__geo_interface__`` attributes so shapely
    does not need to be installed for detection to work.
    """
    return hasattr(obj, "geom_type") and hasattr(obj, "__geo_interface__")


def _get_geom_type(geom: Any) -> str:
    return str(geom.geom_type)


def shapely_point_to_cartesian3(geom: Any) -> Any:
    """Convert a shapely Point to a Cartesian3FromDegrees.

    Uses ``geom.z`` as the height if present (3D Point), otherwise 0.
    """
    from cesiumkit.coordinates import Cartesian3

    x = float(geom.x)
    y = float(geom.y)
    z = float(geom.z) if geom.has_z else 0.0
    return Cartesian3.from_degrees(x, y, z)


def shapely_line_to_positions(geom: Any) -> list[Any]:
    """Convert a shapely LineString or LinearRing to a list of Cartesian3FromDegrees."""
    from cesiumkit.coordinates import Cartesian3

    positions: list[Any] = []
    has_z = bool(getattr(geom, "has_z", False))
    for coord in geom.coords:
        lon = float(coord[0])
        lat = float(coord[1])
        height = float(coord[2]) if has_z and len(coord) >= 3 else 0.0
        positions.append(Cartesian3.from_degrees(lon, lat, height))
    return positions


def shapely_polygon_to_hierarchy(geom: Any) -> Any:
    """Convert a shapely Polygon to a PolygonHierarchy, preserving holes."""
    from cesiumkit.entities.polygon import PolygonHierarchy

    exterior = shapely_line_to_positions(geom.exterior)
    holes = None
    interiors = list(getattr(geom, "interiors", []))
    if interiors:
        holes = [PolygonHierarchy(positions=shapely_line_to_positions(ring)) for ring in interiors]
    return PolygonHierarchy(positions=exterior, holes=holes)


def shapely_to_entities(geom: Any, **entity_kwargs: Any) -> list[Any]:
    """Convert a shapely geometry to a list of cesiumkit Entities.

    Dispatches by geometry type:
    - Point -> one Entity with a position and a default PointGraphics
    - LineString / LinearRing -> one Entity with PolylineGraphics
    - Polygon -> one Entity with PolygonGraphics
    - MultiPoint / MultiLineString / MultiPolygon -> list of Entities (one per part)
    - GeometryCollection -> flattened list of Entities

    Extra keyword arguments are forwarded to the Entity constructor.
    For Multi* geometries, the same kwargs are shared across all parts.
    """
    from cesiumkit.entities._base import Entity
    from cesiumkit.entities.point import PointGraphics
    from cesiumkit.entities.polygon import PolygonGraphics
    from cesiumkit.entities.polyline import PolylineGraphics

    geom_type = _get_geom_type(geom)

    if geom_type == "Point":
        kwargs = dict(entity_kwargs)
        kwargs.setdefault("point", PointGraphics(pixel_size=8))
        return [Entity(position=shapely_point_to_cartesian3(geom), **kwargs)]

    if geom_type in ("LineString", "LinearRing"):
        kwargs = dict(entity_kwargs)
        kwargs.setdefault("polyline", PolylineGraphics(positions=shapely_line_to_positions(geom), width=2))
        return [Entity(**kwargs)]

    if geom_type == "Polygon":
        kwargs = dict(entity_kwargs)
        kwargs.setdefault("polygon", PolygonGraphics(hierarchy=shapely_polygon_to_hierarchy(geom)))
        return [Entity(**kwargs)]

    if geom_type in ("MultiPoint", "MultiLineString", "MultiPolygon", "GeometryCollection"):
        entities: list[Any] = []
        for part in geom.geoms:
            entities.extend(shapely_to_entities(part, **entity_kwargs))
        return entities

    raise ValueError(f"Unsupported shapely geometry type: {geom_type}")
