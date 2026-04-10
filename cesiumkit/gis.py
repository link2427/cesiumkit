"""GeoPandas / pandas integration for cesiumkit.

Convert ``GeoDataFrame`` and plain ``DataFrame`` objects into lists of
``Entity`` in one call. GeoPandas and shapely are optional dependencies —
install with ``pip install cesiumkit[gis]``.
"""

from __future__ import annotations

from typing import Any

from cesiumkit._shapely import (
    is_shapely_geom,
    shapely_line_to_positions,
    shapely_point_to_cartesian3,
    shapely_polygon_to_hierarchy,
)
from cesiumkit.color import Color
from cesiumkit.coordinates import Cartesian3
from cesiumkit.entities._base import Entity
from cesiumkit.entities.point import PointGraphics
from cesiumkit.entities.polygon import PolygonGraphics
from cesiumkit.entities.polyline import PolylineGraphics


def _resolve_color(value: Any) -> Color:
    """Accept a Color, a CSS/hex string, or a named color string and return a Color."""
    if isinstance(value, Color):
        return value
    if isinstance(value, str):
        # Try named color first (e.g. "RED" or "red")
        name = value.upper()
        named = getattr(Color, name, None)
        if isinstance(named, Color):
            return named
        # Fall back to CSS parsing
        return Color.from_css(value)
    raise TypeError(f"Cannot interpret {value!r} as a Color")


def _get_row_value(row: Any, column: str | None, default: Any = None) -> Any:
    """Pull a column value from a pandas/GeoPandas row, or return default."""
    if column is None:
        return default
    try:
        val = row[column]
    except (KeyError, IndexError):
        return default
    # Handle NaN gracefully (pandas uses NaN for missing numbers)
    try:
        import math

        if isinstance(val, float) and math.isnan(val):
            return default
    except Exception:
        pass
    return val


def _entity_from_geom(
    geom: Any,
    row: Any,
    *,
    name: str | None,
    description: str | None,
    color: Color | None,
    fill_alpha: float,
    stroke: Color | None,
    stroke_width: float,
    height: float,
    extruded_height: float | None,
    point_pixel_size: float,
) -> list[Entity]:
    """Build a list of Entities from a single shapely geometry + its row."""
    geom_type = geom.geom_type

    # Point-like
    if geom_type == "Point":
        point = PointGraphics(
            pixel_size=point_pixel_size,
            color=color,
            outline_color=stroke,
            outline_width=stroke_width,
        )
        return [
            Entity(
                name=name,
                description=description,
                position=shapely_point_to_cartesian3(geom),
                point=point,
            )
        ]

    if geom_type == "MultiPoint":
        entities: list[Entity] = []
        for part in geom.geoms:
            entities.extend(
                _entity_from_geom(
                    part,
                    row,
                    name=name,
                    description=description,
                    color=color,
                    fill_alpha=fill_alpha,
                    stroke=stroke,
                    stroke_width=stroke_width,
                    height=height,
                    extruded_height=extruded_height,
                    point_pixel_size=point_pixel_size,
                )
            )
        return entities

    # Line-like
    if geom_type in ("LineString", "LinearRing"):
        polyline = PolylineGraphics(
            positions=shapely_line_to_positions(geom),
            width=stroke_width,
            material=stroke or color,
        )
        return [Entity(name=name, description=description, polyline=polyline)]

    if geom_type == "MultiLineString":
        return [
            e
            for part in geom.geoms
            for e in _entity_from_geom(
                part,
                row,
                name=name,
                description=description,
                color=color,
                fill_alpha=fill_alpha,
                stroke=stroke,
                stroke_width=stroke_width,
                height=height,
                extruded_height=extruded_height,
                point_pixel_size=point_pixel_size,
            )
        ]

    # Polygon-like
    if geom_type == "Polygon":
        fill_color = color.with_alpha(fill_alpha) if color is not None else None
        polygon = PolygonGraphics(
            hierarchy=shapely_polygon_to_hierarchy(geom),
            material=fill_color,
            outline=True if stroke is not None else None,
            outline_color=stroke,
            outline_width=stroke_width if stroke is not None else None,
            height=height if height != 0 else None,
            extruded_height=extruded_height,
        )
        return [Entity(name=name, description=description, polygon=polygon)]

    if geom_type == "MultiPolygon":
        return [
            e
            for part in geom.geoms
            for e in _entity_from_geom(
                part,
                row,
                name=name,
                description=description,
                color=color,
                fill_alpha=fill_alpha,
                stroke=stroke,
                stroke_width=stroke_width,
                height=height,
                extruded_height=extruded_height,
                point_pixel_size=point_pixel_size,
            )
        ]

    if geom_type == "GeometryCollection":
        return [
            e
            for part in geom.geoms
            for e in _entity_from_geom(
                part,
                row,
                name=name,
                description=description,
                color=color,
                fill_alpha=fill_alpha,
                stroke=stroke,
                stroke_width=stroke_width,
                height=height,
                extruded_height=extruded_height,
                point_pixel_size=point_pixel_size,
            )
        ]

    raise ValueError(f"Unsupported geometry type: {geom_type}")


def geodataframe_to_entities(
    gdf: Any,
    *,
    name_column: str | None = None,
    description_column: str | None = None,
    color: Any = None,
    color_column: str | None = None,
    fill_alpha: float = 0.5,
    stroke: Any = None,
    stroke_width: float = 2.0,
    height: float = 0.0,
    height_column: str | None = None,
    extruded_height_column: str | None = None,
    point_pixel_size: float = 8.0,
) -> list[Entity]:
    """Convert a ``geopandas.GeoDataFrame`` to a list of ``Entity`` objects.

    The GeoDataFrame is reprojected to EPSG:4326 (WGS84 lon/lat) if a CRS is
    set and it is not already 4326.

    Args:
        gdf: The ``geopandas.GeoDataFrame`` to convert.
        name_column: Column to use for each entity's ``name``.
        description_column: Column to use for each entity's ``description``.
        color: Default color for all entities. Accepts a ``Color``, a CSS/hex
            string, or a named-color string (e.g. ``"RED"``).
        color_column: Column with a per-feature color (same types as ``color``).
            Overrides ``color`` on a per-row basis.
        fill_alpha: Alpha value for polygon fill (default 0.5).
        stroke: Outline color for polygons / line color for polylines.
        stroke_width: Outline / polyline width in pixels (default 2).
        height: Base height for polygons if no column is specified.
        height_column: Column with per-row polygon base heights.
        extruded_height_column: Column with per-row polygon extruded heights.
            Use this to extrude polygons into 3D volumes (e.g. building footprints).
        point_pixel_size: Size in pixels for Point entities.

    Returns:
        A list of ``Entity`` objects ready to add to a ``Viewer``.

    Raises:
        ImportError: if geopandas is not installed.
        ValueError: if the GeoDataFrame contains an unsupported geometry type.
    """
    try:
        import geopandas as gpd  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "geopandas is required for geodataframe_to_entities. Install with `pip install cesiumkit[gis]`."
        ) from e

    # Reproject to WGS84 if needed
    if getattr(gdf, "crs", None) is not None:
        try:
            if gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
        except Exception:
            # If CRS introspection fails, try to reproject anyway
            gdf = gdf.to_crs(epsg=4326)

    default_color = _resolve_color(color) if color is not None else None
    stroke_color = _resolve_color(stroke) if stroke is not None else None

    entities: list[Entity] = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or not is_shapely_geom(geom):
            continue

        row_name = _get_row_value(row, name_column)
        row_name = str(row_name) if row_name is not None else None
        row_desc = _get_row_value(row, description_column)
        row_desc = str(row_desc) if row_desc is not None else None

        row_color = default_color
        if color_column is not None:
            col_val = _get_row_value(row, color_column)
            if col_val is not None:
                try:
                    row_color = _resolve_color(col_val)
                except Exception:
                    pass

        row_height = height
        if height_column is not None:
            h = _get_row_value(row, height_column)
            if h is not None:
                row_height = float(h)

        row_extruded = None
        if extruded_height_column is not None:
            e = _get_row_value(row, extruded_height_column)
            if e is not None:
                row_extruded = float(e)

        entities.extend(
            _entity_from_geom(
                geom,
                row,
                name=row_name,
                description=row_desc,
                color=row_color,
                fill_alpha=fill_alpha,
                stroke=stroke_color,
                stroke_width=stroke_width,
                height=row_height,
                extruded_height=row_extruded,
                point_pixel_size=point_pixel_size,
            )
        )

    return entities


def dataframe_to_entities(
    df: Any,
    lon_col: str,
    lat_col: str,
    *,
    height_col: str | None = None,
    name_column: str | None = None,
    description_column: str | None = None,
    color: Any = None,
    color_column: str | None = None,
    point_pixel_size: float = 8.0,
) -> list[Entity]:
    """Convert a plain ``pandas.DataFrame`` with lon/lat columns to point entities.

    This is a convenience wrapper for the most common case — a CSV of points —
    that avoids requiring GeoPandas. Only produces ``Point`` entities.

    Args:
        df: A ``pandas.DataFrame``.
        lon_col: Name of the longitude column.
        lat_col: Name of the latitude column.
        height_col: Optional column for point heights (meters above ellipsoid).
        name_column: Column to use for each entity's ``name``.
        description_column: Column to use for each entity's ``description``.
        color: Default color for all points.
        color_column: Column for per-feature color.
        point_pixel_size: Point size in pixels.

    Returns:
        A list of ``Entity`` objects with ``PointGraphics`` attached.
    """
    default_color = _resolve_color(color) if color is not None else None

    entities: list[Entity] = []
    for _, row in df.iterrows():
        lon = float(row[lon_col])
        lat = float(row[lat_col])
        h = float(row[height_col]) if height_col is not None else 0.0

        row_name = _get_row_value(row, name_column)
        row_name = str(row_name) if row_name is not None else None
        row_desc = _get_row_value(row, description_column)
        row_desc = str(row_desc) if row_desc is not None else None

        row_color = default_color
        if color_column is not None:
            col_val = _get_row_value(row, color_column)
            if col_val is not None:
                try:
                    row_color = _resolve_color(col_val)
                except Exception:
                    pass

        entities.append(
            Entity(
                name=row_name,
                description=row_desc,
                position=Cartesian3.from_degrees(lon, lat, h),
                point=PointGraphics(pixel_size=point_pixel_size, color=row_color),
            )
        )

    return entities
