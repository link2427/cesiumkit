"""Local raster tile serving for :meth:`cesiumkit.Viewer.add_raster`.

Dependencies (``rio-tiler`` / ``rasterio`` / ``xarray``) live in the
``[raster]`` extra and are imported lazily so the core package stays
dependency-light. The tile endpoint serves Web Mercator XYZ tiles, matching
Cesium's default ``WebMercatorTilingScheme``.
"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from typing import Any

from cesiumkit.utils import generate_id

_TILE_SIZE = 256


class RasterSource:
    """A raster served as Web Mercator tiles by the local viewer server.

    Accepts either a file path (any format rasterio can open) or an
    ``xarray.DataArray`` with georeferencing.
    """

    def __init__(self, source: str | Path | Any, *, name: str | None = None) -> None:
        self.id = f"raster-{generate_id()}"
        self._source = source
        self.path = str(source) if isinstance(source, (str, Path)) else None
        self.name = name or (Path(self.path).stem if self.path else "raster")
        self._reader: Any = None
        self._lock = threading.Lock()

    def _open_reader(self):
        from rio_tiler.io import Reader, XarrayReader

        if self._reader is None:
            with self._lock:
                if self._reader is None:
                    if self.path is not None:
                        # rio-tiler's attrs-based __init__ has an undetectable
                        # NOTHING sentinel default; pyright treats it as required.
                        self._reader = Reader(self.path)  # pyright: ignore[reportCallIssue]
                    else:
                        self._reader = XarrayReader(self._source)  # pyright: ignore[reportCallIssue]
        return self._reader

    def tile(self, z: int, x: int, y: int) -> bytes | None:
        """Return a PNG tile, or None when out of range."""
        reader = self._open_reader()
        try:
            image = reader.tile(x, y, z, tilesize=_TILE_SIZE)
        except Exception:
            return None
        return image.render(img_format="PNG")

    def close(self) -> None:
        if self._reader is not None:
            closer = getattr(self._reader, "close", None)
            if callable(closer):
                closer()
            self._reader = None


def aggregate_points_to_raster(
    gdf: Any,
    *,
    plot_width: int = 1024,
    plot_height: int = 512,
    colormap: list[str] | None = None,
) -> str:
    """Aggregate a point GeoDataFrame with datashader into a temp GeoTIFF.

    Returns the path to a 3-band RGB GeoTIFF in EPSG:4326 covering the
    GeoDataFrame's bounds, ready for :class:`RasterSource`.

    Args:
        gdf: Point GeoDataFrame to aggregate.
        plot_width: Aggregation canvas width in pixels.
        plot_height: Aggregation canvas height in pixels.
        colormap: List of CSS colors for the shading ramp; defaults to a
            dark-blue-to-red ramp.
    """
    import datashader as ds
    import datashader.transfer_functions as tf
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    if "geometry" not in gdf.columns:
        raise ValueError("gdf must be a GeoDataFrame with a geometry column")
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    west, south, east, north = gdf.total_bounds

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
    return path


__all__ = [
    "RasterSource",
    "aggregate_points_to_raster",
]
