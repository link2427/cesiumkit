# Changelog

All notable changes to cesiumkit are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.6.0] - 2026-08-04

### Added

- **Public API audit.** Every module now declares its public surface via
  `__all__`; a CI test enforces that all public names are listed and resolve.
- **CustomDataSource entities.** Attach Python entities to a custom data
  source with `ds.entities.add(...)`; they emit as `ds.entities.add(...)`
  after the data source is added to the viewer (HTML and Jupyter widget).
- `GlobeConfig.show_sky_atmosphere` now controls
  `scene.skyAtmosphere.show` (previously declared but never emitted).
- CI-status badge in the README; a Vulture dead-code gate in the lint job.

### Changed

- `BingMapsImageryProvider.key` and `KmlDataSource.url` are now required
  fields; the old `""` defaults produced providers that always failed.
- Packaging per PEP 639: explicit `license-files`, the deprecated
  `License :: OSI Approved :: MIT License` classifier removed, hatchling
  pinned to `>=1.26`.
- Publish workflow validates artifacts before upload: `twine check` plus a
  fresh-venv sdist install smoke test (import + vendored Cesium present).
- API reference pages added for the `math`, `particle`, and `testing`
  modules.

### Fixed

- Dead code in the widget command handler (unused callback parameters).

## [0.5.0] - 2026-08-04

### Added

- **Entity clustering.** `EntityClusterConfig` groups nearby points,
  billboards, and labels via Cesium's `EntityCollection.clustering`.
- **Camera fit helpers.** `fly_to_entities()` and `fly_to_bounding_sphere()`
  on both `Camera` and `Viewer`.
- **3D Tiles styling.** New `Cesium3DTileStyle` applies per-feature color,
  show, and point-size conditions; `Cesium3DTileset` options (`show`,
  `maximumScreenSpaceError`, `maximumMemoryUsage`, `shadows`) now serialize
  when explicitly set.
- **Rasters & large data.** `Viewer.add_raster()` displays GeoTIFF/COG files
  or xarray `DataArray`s as Web Mercator tiles (rio-tiler, `[raster]` extra,
  served by `show()`); `Viewer.add_points()` aggregates large point sets via
  datashader (`[datashader]` extra); `gis.geodataframe_to_czml_packets()`
  streams chunked CZML batches through `stream_czml()`.
- **Headless render testing.** `cesiumkit.testing` provides
  `render_state()`/`render_screenshot()`/`serve()` over playwright, a
  `playwright_browser` pytest fixture, and `scripts/render_examples.py`;
  a CI `render-check` job renders every show-based example headlessly and
  uploads the PNGs as artifacts.
- **Jupyter widget.** `Viewer.to_widget()` returns a `CesiumKitWidget`
  (anywidget, `[widget]` extra) with live clock control, click events, and
  screenshots over comm messages — no HTTP server needed.

### Changed

- CI test matrix now installs the GIS extras, so the GeoPandas/Shapely tests
  actually run, and enforces a coverage gate (`--cov-fail-under=75`, set to
  the coverage CI measures with the default extras installed).
- `scripts/fetch_cesium.py` bundles Cesium's `LICENSE.md`/`NOTICE.md`
  (Apache-2.0) alongside the vendored build and reports its size.
- CONTRIBUTING documents the release process, including linking the
  changelog in release notes.

## [0.4.0] - 2026-08-04

### Added

- **Bundled offline Cesium build.** `scripts/fetch_cesium.py` downloads the
  official CesiumJS release into the package; when present, `show()` serves
  Cesium.js and the NaturalEarthII fallback imagery locally, so viewers work
  fully offline and in air-gapped environments. The publish workflow fetches
  it before building, so the wheel ships with offline support.
- **Headless render smoke test.** `scripts/smoke_render.py` loads a viewer in
  headless Chromium (playwright) and verifies the globe initializes and
  renders, for CI/headless environments.

### Changed

- **CesiumJS upgraded from 1.119 to 1.144.** The imagery provider is now
  passed to the Viewer as `baseLayer` wrapped in an `ImageryLayer` (the old
  `imageryProvider` option was removed in Cesium 1.144), and terrain
  providers are assigned to `scene.terrainProvider` after construction via
  their async factory methods (`CesiumTerrainProvider.fromUrl`,
  `createWorldTerrainAsync`).
- `IonTerrainProvider.asset_id` is now honored: non-default asset ids emit
  `CesiumTerrainProvider.fromIonAssetId(...)` instead of always using world
  terrain.
- Static HTML export (`to_html()`/`save()`) and Jupyter embedding still load
  Cesium from the CDN; only `show()` serves the bundled build.

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
