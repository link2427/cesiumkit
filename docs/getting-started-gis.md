# GeoDataFrame to globe in 3 lines

cesiumkit v0.2.0 adds native support for [GeoPandas](https://geopandas.org)
and [Shapely](https://shapely.readthedocs.io). If you have a `GeoDataFrame`,
you can drop it on the globe with a single call.

## Install

```bash
pip install cesiumkit[gis]
```

This pulls in `geopandas` and `shapely`. If you already have them, the base
`pip install cesiumkit` is all you need.

## Minimal example

```python
import geopandas as gpd
import cesiumkit

gdf = gpd.read_file("countries.geojson")
viewer = cesiumkit.Viewer()
viewer.add_geodataframe(gdf, name_column="NAME")
viewer.show()
```

That's it. The GeoDataFrame is reprojected to WGS84 if it has a different
CRS, then each row becomes an `Entity` with the appropriate graphics:

- `Point` / `MultiPoint` → `PointGraphics`
- `LineString` / `MultiLineString` → `PolylineGraphics`
- `Polygon` / `MultiPolygon` → `PolygonGraphics` (with holes preserved)

## Styling by column

Use column values to drive per-feature styling:

```python
viewer.add_geodataframe(
    gdf,
    name_column="NAME",
    description_column="DESCRIPTION",
    color_column="color_hex",           # e.g. "#ff8800" per row
    fill_alpha=0.4,
    stroke=cesiumkit.Color.WHITE,
    stroke_width=2,
    extruded_height_column="height_m",  # polygons become 3D prisms
)
```

`color_column` accepts `Color` instances, CSS/hex strings like `"#ff8800"`,
or named colors like `"RED"`.

## Plain DataFrames

If you don't have a GeoDataFrame but you do have a CSV with lon/lat columns:

```python
import pandas as pd

df = pd.read_csv("cities.csv")  # name, lon, lat, population
viewer.add_dataframe(
    df,
    lon_col="lon",
    lat_col="lat",
    name_column="name",
    color=cesiumkit.Color.GOLD,
    point_pixel_size=10,
)
```

## Using Shapely directly

You can also pass shapely geometries anywhere cesiumkit expects positions —
Pydantic validators auto-convert them:

```python
from shapely.geometry import Point, Polygon
import cesiumkit

viewer.add_entity(cesiumkit.Entity(
    name="HQ",
    position=Point(-74.006, 40.7128),  # shapely Point → Cartesian3
))

viewer.add_entity(cesiumkit.Entity(
    name="Site",
    polygon=cesiumkit.PolygonGraphics(
        hierarchy=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),  # Polygon → hierarchy
        material=cesiumkit.Color.CORNFLOWERBLUE.with_alpha(0.6),
    ),
))
```

Shapely is CRS-naive, so cesiumkit assumes the coordinates are WGS84 lon/lat.
If your shapely geometries are in another CRS, reproject them (e.g. with
`pyproj`) before passing them in — or use `GeoDataFrame` which carries CRS
information and auto-reprojects.
