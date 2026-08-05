# cesiumkit

**3D globe visualizations in Python** — entities, materials, camera, terrain,
imagery, and time-dynamic animation, rendered in your browser via
[CesiumJS](https://cesium.com/cesiumjs/).

[![PyPI version](https://img.shields.io/pypi/v/cesiumkit.svg)](https://pypi.org/project/cesiumkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/cesiumkit.svg)](https://pypi.org/project/cesiumkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/link2427/cesiumkit/actions/workflows/ci.yml/badge.svg)](https://github.com/link2427/cesiumkit/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/website-up-down-green-red/https/link2427.github.io/cesiumkit.svg)](https://link2427.github.io/cesiumkit)
[![Coverage](https://link2427.github.io/cesiumkit/coverage.svg)](https://link2427.github.io/cesiumkit)

![Globe hero](https://link2427.github.io/cesiumkit/images/gallery/01_globe_hero.png)
*A globe rendered with cesiumkit — one `show()` call opens it in your browser.*

## What it is

cesiumkit is a Pythonic, object-oriented API for
[CesiumJS](https://cesium.com/cesiumjs/), the open-source JavaScript library
for 3D globes and maps. Define entities, materials, camera views, terrain,
imagery, and time-dynamic animations in pure Python; the library generates
the page and serves it locally. It plays the same role for 3D globe data
that libraries like folium play for 2D maps.

- **17 entity graphics types** and 9 materials, all as validated Pydantic models
- **Time-dynamic animation** with sampled properties and a clock
- **GeoPandas / Shapely**: drop a `GeoDataFrame` on the globe in one call
- **Rasters & large data**: local GeoTIFFs and datashader-aggregated point sets
- **Live control**: drive the clock, update data, and receive clicks from Python
- **Offline-friendly**: the wheel bundles a Cesium build, so `show()` works without the CDN

## Quickstart

```bash
pip install cesiumkit
```

```python
import cesiumkit

viewer = cesiumkit.Viewer(title="Hello Globe")
viewer.add_entity(
    cesiumkit.Entity(
        name="New York",
        position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
        point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
    )
)
viewer.show()  # opens in your browser; Ctrl+C to stop the server
```

Requires Python 3.10+. The published wheel bundles a Cesium build, so
`show()` works fully offline out of the box.

## Gallery

| | | |
|---|---|---|
| [![Shapes](https://link2427.github.io/cesiumkit/images/gallery/02_shapes.png)](https://link2427.github.io/cesiumkit/gallery/) *Shapes & materials* | [![Cities](https://link2427.github.io/cesiumkit/images/gallery/03_cities.png)](https://link2427.github.io/cesiumkit/gallery/) *Cities* | [![Flight path](https://link2427.github.io/cesiumkit/images/gallery/04_flight_path.png)](https://link2427.github.io/cesiumkit/gallery/) *Flight path* |
| [![GeoPandas](https://link2427.github.io/cesiumkit/images/gallery/05_geopandas.png)](https://link2427.github.io/cesiumkit/gallery/) *GeoPandas* | [![Extruded polygons](https://link2427.github.io/cesiumkit/images/gallery/06_polygon_3d.png)](https://link2427.github.io/cesiumkit/gallery/) *Extruded polygons* | [More →](https://link2427.github.io/cesiumkit/gallery/) |

## Documentation

- [Getting started](https://link2427.github.io/cesiumkit/getting-started/) — install and your first globe
- [Tutorial](https://link2427.github.io/cesiumkit/tutorial/) — build a flight tracker step by step
- [Guide](https://link2427.github.io/cesiumkit/guide/) — GeoPandas, rasters, live control, Jupyter widget
- [Examples](https://link2427.github.io/cesiumkit/examples/) — 11 runnable scripts, one page each
- [API reference](https://link2427.github.io/cesiumkit/api/) — type-annotated, with doctested examples
- [Changelog](CHANGELOG.md)

## Extras & offline use

Optional features ship as install extras:

```bash
pip install "cesiumkit[gis]"         # GeoPandas / Shapely integration
pip install "cesiumkit[raster]"      # local GeoTIFF / COG / DataArray tiles
pip install "cesiumkit[datashader]"  # aggregate millions of points
pip install "cesiumkit[widget]"      # Jupyter widget (anywidget)
```

By default the generated pages load CesiumJS from the CDN. To run fully
offline (air-gapped machines, CI, headless servers), vendor the Cesium build
once — the wheel published to PyPI already includes it:

```bash
python scripts/fetch_cesium.py   # downloads the CesiumJS 1.144 release (~120 MB)
```

Static HTML export and the Jupyter widget load from the CDN. Many features
work without a Cesium Ion token using the bundled NaturalEarthII imagery; for
Bing imagery, world terrain, or 3D Tilesets, get a free token at
[cesium.com/ion](https://cesium.com/ion/) and set it with
`cesiumkit.Ion.set_default_token("...")`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and
how to add new entity types.

## License

The code in this project is licensed under the [MIT License](LICENSE).
