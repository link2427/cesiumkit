# Architecture

_Explanation. How a `Viewer` becomes a running globe, what `show()` serves,
how the Jupyter widget talks to the browser, and where the bundled Cesium
build fits. You do not need this to use cesiumkit; read it when you want
the mental model._

## From Python objects to a page

A `Viewer` is a tree of Pydantic models. Each model knows how to serialize
itself to a CesiumJS expression via `to_js()` — entities, materials,
providers, and configs all do. Rendering walks that tree:

1. `Viewer.to_html()` renders `viewer.html.j2` into one self-contained HTML
   file: a `<script>` block that constructs `Cesium.Viewer(...)` from the
   serialized viewer options, then adds entities, data sources, terrain,
   event handlers, and clock configuration in order.
2. `Viewer.show()` serves that HTML over a local HTTP server and opens the
   browser. The same HTML works standalone — nothing about the generated
   page depends on the server.

## What the local server serves

`show()` runs a `ThreadingHTTPServer` with these routes:

- `/` and `/index.html` — the generated page.
- `/vendor/*` — the bundled Cesium build (see below), served from the
  installed package without copying it.
- `/raster/<id>/{z}/{x}/{y}.png` — tiles for `add_raster` and
  `add_points`.
- `/__cesiumkit_cmd` — the command bridge: Python posts viewer commands
  (set time, update data, screenshot request) as JSON, the page executes
  them, and results come back on `/__cesiumkit_result`.

The command bridge is what makes `set_time()`, `pick()`, `screenshot()`,
and the click callbacks work without rebuilding the page.

## Bundled Cesium and offline mode

Since 0.4.0 the wheel ships the CesiumJS build under
`cesiumkit/vendor/cesium/` (fetched by `scripts/fetch_cesium.py` at release
time). `show()` serves it from `/vendor`, so local pages run fully offline,
including the NaturalEarthII fallback imagery used when no Ion token is
set. `to_html()` output and the Jupyter widget have no server, so they
reference CesiumJS on the CDN instead.

## The Jupyter widget

`Viewer.to_widget()` packages the same serialized viewer tree as widget
state and hands it to a small JavaScript module (ESM) that runs in the
notebook. The ESM evaluates the state into a `Cesium.Viewer`, then opens a
comm channel: Python and the browser exchange JSON messages for clock
control, entity clicks, and screenshot data — the same operations the HTTP
command bridge provides for `show()`, but over the notebook's message
transport instead of HTTP.

## CZML export

For interop with other CesiumJS applications, `CzmlDocument` serializes
entities to CZML packets (`to_list()` / `save()`). Live streaming uses the
same packet format: `stream_czml()` ships batches over the command bridge,
and the page feeds them to a `CzmlDataSource`.

## Testing headlessly

Because everything is generated HTML plus a small server, the whole stack
is testable without a display: `cesiumkit.testing` renders the page in a
headless browser (playwright), checks the scene state, and screenshots the
canvas — the same path the CI `render-check` job uses for the examples.
