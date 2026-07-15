# Changelog

All notable changes to cesiumkit are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-07-14

### Added

- **Live clock control.** `Viewer.set_time()`, `animate()`,
  `set_multiplier()`, and `get_current_time()` control and inspect the clock
  while a viewer is running.
- **Live data updates.** Replace CZML or GeoJSON sources without rebuilding the
  page, poll CZML URLs in the browser, or stream Python-produced CZML batches.
- **Runtime selection and picking.** Select and deselect entities, inspect the
  selected entity, and use `pick()` or `drill_pick()` at screen coordinates.
- **Python click events.** `Viewer.on_click()` sends public entity IDs from the
  browser to Python callbacks, while `wait_for_click()` provides a synchronous
  event interface.
- **Screenshot export.** Capture the live canvas as a PNG file, base64 data, or
  a Pillow image through the optional `[images]` extra.
- **Entity convenience methods.** Add, retrieve, remove, count, and clear
  entities directly through `Viewer`.
- **Plane graphics and particle systems.** Render `PlaneGraphics` on entities
  and add validated `ParticleSystem` scene primitives.
- **Post-processing configuration.** Configure bloom, FXAA, and ambient
  occlusion stages through `SceneConfig`.
- **Encoded heightmap terrain.** WMS and WMTS terrain providers decode
  Terrain-RGB, Terrarium, or grayscale tiles through Cesium's custom heightmap
  provider.
- **Runtime control guide and example.** A new guide documents the server
  lifecycle, clock, live data, selection, click events, and screenshots.

### Changed

- Viewer performance can now be tuned with request-render mode, maximum render
  time change, resolution scale, target frame rate, and renderer-error controls.
- Terrain exaggeration now maps to Cesium's scene-level vertical exaggeration
  API, including relative-height configuration.
- The browser command channel now correlates results and errors, validates
  payloads, and safely supports concurrent commands and event delivery.

### Fixed

- Runtime commands now escape user-provided IDs, URLs, and timestamps before
  inserting them into generated JavaScript.
- Live data replacement targets the first matching data-source type instead of
  assuming it is at collection index zero.
- Python click handling now uses the correct left-click position and Cesium's
  public entity ID instead of private implementation fields.

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
