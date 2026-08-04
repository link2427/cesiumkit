# How to display rasters and large point data

_How-to. Target: a local GeoTIFF as the base imagery layer, and millions of
points aggregated into one tile layer instead of thousands of entities._

Both features serve tiles through the local `show()` server, so they need a
running server — they do not work in static HTML export or the notebook
widget.

## 1. Install the extras

```bash
pip install "cesiumkit[raster]"     # rio-tiler / rasterio / xarray
pip install "cesiumkit[datashader]" # point aggregation
```

## 2. Add a raster as the base layer

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_raster("elevation.tif")  # any path rasterio can open
viewer.show()
```

`add_raster` accepts a file path or a georeferenced `xarray.DataArray` and
sets it as the base imagery layer. Tiles are served from
`/raster/<id>/{z}/{x}/{y}.png` in Web Mercator, matching Cesium's default
tiling scheme.

## 3. Aggregate a huge point set with datashader

```python
viewer.add_points(gdf)  # GeoDataFrame; aggregated to an imagery layer
```

With `aggregation=True` (the default) the points are rasterized with
datashader, which stays responsive for millions of points. Pass
`aggregation=False` to fall back to one entity per point.

## 4. Stream a GeoDataFrame as CZML instead

For moderate-size vector data you can stream batches to the live viewer
without aggregating:

```python
packets = cesiumkit.geodataframe_to_czml_packets(gdf, batch_size=500, color_column="color_hex")
viewer.stream_czml(packets, interval=1.0)
```

## API reference

- ::: cesiumkit.raster
