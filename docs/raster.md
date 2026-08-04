# Rasters & Large Point Data

Display local georeferenced rasters and aggregate huge point sets directly on
the globe. Both features serve tiles through the local ``show()`` server, so
they need a running server (not static HTML export).

Install the extras:

```bash
pip install "cesiumkit[raster]"     # rio-tiler / rasterio / xarray
pip install "cesiumkit[datashader]" # datashader aggregation
```

## Local rasters

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_raster("elevation.tif")  # GeoTIFF / COG path
viewer.show()
```

``add_raster`` accepts a file path (anything rasterio can open) or a
georeferenced ``xarray.DataArray``, and sets it as the base imagery layer.
Tiles are served from ``/raster/<id>/{z}/{x}/{y}.png`` in Web Mercator,
matching Cesium's default tiling scheme.

## Large point data with datashader

```python
viewer.add_points(gdf)  # aggregated to an imagery layer, no per-point entities
```

With ``aggregation=True`` (default) the points are rasterized with
datashader, which stays responsive for millions of points. Pass
``aggregation=False`` to fall back to per-point entities.

## Streaming a GeoDataFrame as CZML

For moderate-size vector data you can stream a GeoDataFrame to the live
viewer in batches instead of aggregating:

```python
packets = cesiumkit.geodataframe_to_czml_packets(gdf, batch_size=500, color_column="color_hex")
viewer.stream_czml(packets, interval=1.0)
```

::: cesiumkit.raster
