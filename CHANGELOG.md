# Changelog

All notable changes to cesiumkit are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-04-10

### Added

- **GeoPandas integration.** `cesiumkit.geodataframe_to_entities(gdf, ...)` and
  `Viewer.add_geodataframe(gdf, ...)` convert a `GeoDataFrame` into entities in
  a single call. Handles Point / LineString / Polygon / Multi* geometries,
  auto-reprojects non-WGS84 CRSes to EPSG:4326, and supports per-feature
  styling from columns (`name_column`, `color_column`, `height_column`,
  `extruded_height_column`).
- **Plain DataFrame integration.** `cesiumkit.dataframe_to_entities(df, lon_col,
  lat_col, ...)` and `Viewer.add_dataframe(...)` for the "CSV of points" case
  without requiring GeoPandas.
- **Shapely geometry support.** Shapely `Point`, `LineString`, `LinearRing`,
  and `Polygon` (with holes) are auto-converted to cesiumkit types via Pydantic
  field validators on `Entity.position`, `PolygonGraphics.hierarchy`, and
  `PolylineGraphics.positions`. Also adds `Cartesian3.from_shapely()` for
  explicit conversion.
- **Optional `[gis]` install extra:** `pip install cesiumkit[gis]` pulls in
  `geopandas>=0.14` and `shapely>=2.0`.
- **Visual gallery.** Six runnable gallery scripts in `scripts/gallery/` and
  a playwright-based orchestrator `scripts/generate_gallery.py` that renders
  each one to a PNG. A new `.github/workflows/gallery.yml` workflow
  regenerates the images on release or manual trigger.
- **Gallery page in docs** (`docs/gallery.md`) and hero image + gallery grid
  in the README.
- **GIS tutorial page** (`docs/getting-started-gis.md`) walking through
  GeoDataFrame → globe in three lines.
- **API reference page for `cesiumkit.gis`** (`docs/api/gis.md`).

### Changed

- `docs.yml` now fetches the latest gallery images from the `gallery-images`
  branch before building the site, and installs the `[gis]` extra so the
  GeoPandas/Shapely API docs can be introspected by mkdocstrings.

### Fixed

- PyPI project URLs no longer point to the stale `jacobs-github` namespace —
  they were already fixed in the repo but had not yet shipped to PyPI.

## [0.1.0] - 2026-04-06

Initial public release.
