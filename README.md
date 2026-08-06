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
- **Offline-friendly**: published wheels bundle Cesium for local `show()` sessions

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

Requires Python 3.10+. Published wheels bundle Cesium, so `Viewer.show()`
does not need to download CesiumJS. A fully offline scene must also avoid
remote imagery, terrain, data sources, and Cesium Ion resources.

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
pip install "cesiumkit[datashader]"  # point aggregation (includes GIS/raster deps)
pip install "cesiumkit[widget]"      # Jupyter widget (anywidget)
pip install "cesiumkit[testing]"     # headless Chromium render helpers
```

Published wheels already include the checksum-verified CesiumJS 1.144 build.
`Viewer.show()` serves that local build and the bundled NaturalEarthII
imagery; it can run without network access when the viewer has no remote
resources configured. A source checkout intentionally omits the large vendor
directory, so fetch it before testing an offline local server:

```bash
python scripts/fetch_cesium.py   # verifies and downloads CesiumJS 1.144 (~123 MB)
```

`to_html()`/`save()` and the Jupyter widget intentionally reference the CDN;
placing the vendor folder next to a static export does not make it offline.
For Bing imagery, world terrain, or 3D Tilesets, get a free token at
[cesium.com/ion](https://cesium.com/ion/) and set it with
`cesiumkit.Ion.set_default_token("...")`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and
how to add new entity types.

Please follow the [security policy](SECURITY.md) for vulnerability reports.

## License

The code in this project is licensed under the [MIT License](LICENSE).
