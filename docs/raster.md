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

`add_raster` accepts a file path or a georeferenced `xarray.DataArray`, and
sets it as the base imagery layer.

=== "From a file"

    ```python
    import cesiumkit

    viewer = cesiumkit.Viewer()
    viewer.add_raster("elevation.tif")  # any path rasterio can open
    viewer.show()
    ```

=== "From an xarray.DataArray"

    ```python
    import xarray as xr

    da = xr.open_dataarray("elevation.nc")  # must be georeferenced
    viewer = cesiumkit.Viewer()
    viewer.add_raster(da)
    viewer.show()
    ```

Tiles are served from `/raster/<id>/{z}/{x}/{y}.png` in Web Mercator,
matching Cesium's default tiling scheme.

## 3. Stack layers and tune their opacity

The first raster becomes the base layer; each raster you add after that
stacks on top of it. Every layer takes its own opacity (0.0 to 1.0) and
an optional maximum zoom level:

```python
viewer.add_raster("elevation.tif", opacity=0.6)
viewer.add_raster("landcover.tif", name="landcover", opacity=0.8, maximum_level=16)
```

Remote WMTS services (many national map portals expose one) stack the
same way with `add_wmts_layer`:

```python
viewer.add_wmts_layer(
    "https://example.com/wmts",
    layer="topo",
    style="default",
    tile_matrix_set="EPSG:3857",
    opacity=0.7,
)
```

## 4. Aggregate a huge point set with datashader

With `aggregation=True` (the default) the points are rasterized with
datashader, which stays responsive for millions of points. `colormap`
controls the shading ramp, `plot_width`/`plot_height` the aggregation
canvas:

```python
viewer.add_points(
    gdf,
    colormap=["#000000", "#440154", "#fde725"],
    plot_width=1024,
    plot_height=512,
)
```

Pass `aggregation=False` to fall back to one entity per point.

## 5. Stream a GeoDataFrame as CZML instead

For moderate-size vector data you can stream batches to the live viewer
without aggregating:

```python
packets = cesiumkit.geodataframe_to_czml_packets(gdf, batch_size=500, color_column="color_hex")
viewer.stream_czml(packets, interval=1.0)
```

## API reference

- ::: cesiumkit.raster
