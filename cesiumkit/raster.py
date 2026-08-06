"""Local raster tile serving for :meth:`cesiumkit.Viewer.add_raster`.

Dependencies (``rio-tiler`` / ``rasterio`` / ``xarray``) live in the
``[raster]`` extra and are imported lazily so the core package stays
dependency-light. The tile endpoint serves Web Mercator XYZ tiles, matching
Cesium's default ``WebMercatorTilingScheme``.
"""

from __future__ import annotations

import tempfile
import threading
from collections import OrderedDict
from math import isfinite
from os import PathLike
from pathlib import Path
from typing import Any

from cesiumkit.utils import generate_id

_TILE_SIZE = 256


class RasterRenderError(RuntimeError):
    """A raster backend failed while rendering a tile."""


class RasterSource:
    """A raster served as Web Mercator tiles by the local viewer server.

    Accepts either a file path (any format rasterio can open) or an
    ``xarray.DataArray`` with georeferencing. Rendered tiles are cached
    (LRU) so repeated requests avoid re-rendering.
    """

    def __init__(
        self,
        source: str | PathLike[str] | Any,
        *,
        name: str | None = None,
        tile_cache_size: int = 512,
    ) -> None:
        if type(tile_cache_size) is not int or tile_cache_size <= 0:
            raise ValueError("tile_cache_size must be a positive integer")

        self._require_dependencies()
        self.id = f"raster-{generate_id()}"
        self._source = source
        if isinstance(source, (str, PathLike)):
            path = Path(source).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"Raster source does not exist or is not a file: {path}")
            self._validate_raster_path(path)
            self.path = str(path.resolve())
        else:
            self._validate_data_array(source)
            self.path = None
        self.name = name or (Path(self.path).stem if self.path else "raster")
        # A single lock protects both the cache and rendering. rio-tiler
        # readers wrap Rasterio/GDAL state, which must be opened, used, and
        # closed in the same request thread.
        self._lock = threading.RLock()
        self.tile_cache_size = tile_cache_size
        self._tile_cache: OrderedDict[tuple[int, int, int], bytes] = OrderedDict()
        self._closed = False
        self._remove_path_on_close = False

    @staticmethod
    def _require_dependencies() -> None:
        try:
            import rasterio  # noqa: F401
            import xarray  # noqa: F401
            from rio_tiler import io as rio_tiler_io  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "Raster support requires `pip install cesiumkit[raster]` (rio-tiler, rasterio, and xarray)."
            ) from exc

    @staticmethod
    def _validate_data_array(source: Any) -> None:
        import xarray as xr

        if not isinstance(source, xr.DataArray):
            raise TypeError("source must be a local raster path or xarray.DataArray")

    @staticmethod
    def _validate_raster_path(path: Path) -> None:
        import rasterio

        try:
            with rasterio.open(path) as dataset:
                if dataset.crs is None:
                    raise ValueError("Raster source must define a coordinate reference system")
                if dataset.width <= 0 or dataset.height <= 0:
                    raise ValueError("Raster source must have positive dimensions")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Unable to open raster source: {path}") from exc

    def _new_reader(self) -> Any:
        from rio_tiler.io import Reader, XarrayReader

        if self.path is not None:
            # rio-tiler's attrs-based __init__ has an undetectable NOTHING
            # sentinel default; pyright treats it as required.
            return Reader(self.path)  # pyright: ignore[reportCallIssue]
        return XarrayReader(self._source)  # pyright: ignore[reportCallIssue]

    def _mark_owned_path(self) -> None:
        """Mark an aggregate GeoTIFF for deletion when this source closes."""
        if self.path is None:
            raise RuntimeError("Only file-backed rasters can own a temporary path")
        self._remove_path_on_close = True

    @staticmethod
    def _is_out_of_bounds(exc: Exception) -> bool:
        """Return whether rio-tiler identified the requested tile as absent."""
        try:
            from rio_tiler.errors import TileOutsideBounds
        except ImportError:  # pragma: no cover - compatibility with older rio-tiler
            return False
        return isinstance(exc, TileOutsideBounds)

    def tile(self, z: int, x: int, y: int) -> bytes | None:
        """Return a PNG tile, or None when out of range. Results are cached."""
        if any(type(value) is not int for value in (z, x, y)):
            raise TypeError("tile coordinates must be integers")
        if z < 0 or x < 0 or y < 0 or z > 30 or x >= 1 << z or y >= 1 << z:
            return None
        key = (z, x, y)
        with self._lock:
            if self._closed:
                raise RuntimeError("RasterSource is closed")
            cached = self._tile_cache.get(key)
            if cached is not None:
                self._tile_cache.move_to_end(key)
                return cached

            reader = None
            try:
                reader = self._new_reader()
                image = reader.tile(x, y, z, tilesize=_TILE_SIZE)
                body = image.render(img_format="PNG")
            except Exception as exc:
                if self._is_out_of_bounds(exc):
                    return None
                raise RasterRenderError(f"Unable to render raster tile {z}/{x}/{y}") from exc
            finally:
                if reader is not None:
                    closer = getattr(reader, "close", None)
                    if callable(closer):
                        closer()

            self._tile_cache[key] = body
            self._tile_cache.move_to_end(key)
            while len(self._tile_cache) > self.tile_cache_size:
                self._tile_cache.popitem(last=False)
        return body

    def clear_cache(self) -> None:
        """Drop all cached tiles."""
        with self._lock:
            self._tile_cache.clear()

    @property
    def cached_tiles(self) -> int:
        """Number of tiles currently held in the cache."""
        with self._lock:
            return len(self._tile_cache)

    def close(self) -> None:
        """Release cached data and remove a viewer-owned aggregate GeoTIFF."""
        path_to_remove: Path | None = None
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._tile_cache.clear()
            if self._remove_path_on_close and self.path is not None:
                path_to_remove = Path(self.path)

        if path_to_remove is not None:
            try:
                path_to_remove.unlink(missing_ok=True)
            except OSError:
                # Cleanup must be best-effort: a consumer may have removed or
                # retained the file independently on Windows.
                pass

    def __enter__(self) -> RasterSource:
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()


def aggregate_points_to_raster(
    gdf: Any,
    *,
    plot_width: int = 1024,
    plot_height: int = 512,
    colormap: list[str] | None = None,
) -> str:
    """Aggregate a point GeoDataFrame with datashader into a temp GeoTIFF.

    Returns the path to a temporary 3-band RGB GeoTIFF in EPSG:4326 covering
    the GeoDataFrame's bounds, ready for :class:`RasterSource`. The caller
    owns that path and must remove it when finished; :meth:`Viewer.add_points`
    handles this lifecycle automatically.

    Args:
        gdf: Point GeoDataFrame to aggregate.
        plot_width: Aggregation canvas width in pixels.
        plot_height: Aggregation canvas height in pixels.
        colormap: List of CSS colors for the shading ramp; defaults to a
            dark-blue-to-red ramp.
    """
    if type(plot_width) is not int or plot_width <= 0:
        raise ValueError("plot_width must be a positive integer")
    if type(plot_height) is not int or plot_height <= 0:
        raise ValueError("plot_height must be a positive integer")
    if "geometry" not in gdf.columns:
        raise ValueError("gdf must be a GeoDataFrame with a geometry column")
    if gdf.empty:
        raise ValueError("gdf must contain at least one point")
    if gdf.crs is None:
        raise ValueError("gdf must define a coordinate reference system")
    if any(getattr(geometry, "geom_type", None) != "Point" or geometry.is_empty for geometry in gdf.geometry):
        raise ValueError("gdf must contain only non-empty Point geometries")
    if colormap is not None and (
        not isinstance(colormap, list)
        or not colormap
        or any(not isinstance(color, str) or not color for color in colormap)
    ):
        raise ValueError("colormap must be a non-empty list of CSS color strings")

    import datashader as ds
    import datashader.transfer_functions as tf
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    west, south, east, north = gdf.total_bounds
    if not all(isfinite(float(value)) for value in (west, south, east, north)):
        raise ValueError("gdf must have finite geographic bounds")
    if west < -180 or east > 180 or south < -90 or north > 90:
        raise ValueError("gdf coordinates must be within WGS84 longitude/latitude bounds")
    if west == east:
        west = max(-180.0, west - 1e-6)
        east = min(180.0, east + 1e-6)
    if south == north:
        south = max(-90.0, south - 1e-6)
        north = min(90.0, north + 1e-6)

    import pandas as pd

    points = pd.DataFrame({"x": gdf.geometry.x, "y": gdf.geometry.y})
    canvas = ds.Canvas(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=(west, east),
        y_range=(south, north),
    )
    aggregate = canvas.points(points, "x", "y", agg=ds.count())
    cmap = colormap or ["darkblue", "cyan", "yellow", "red"]
    image = tf.shade(aggregate, cmap=cmap, how="eq_hist")
    pixels = np.array(image.to_pil().convert("RGB"))

    fd, path = tempfile.mkstemp(suffix=".tif", prefix="cesiumkit_agg_")
    import os

    os.close(fd)
    transform = from_bounds(west, south, east, north, plot_width, plot_height)
    try:
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=plot_height,
            width=plot_width,
            count=3,
            dtype="uint8",
            crs="EPSG:4326",
            transform=transform,
        ) as dst:
            dst.write(pixels.transpose(2, 0, 1))
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise
    return path


__all__ = [
    "RasterSource",
    "RasterRenderError",
    "aggregate_points_to_raster",
]
