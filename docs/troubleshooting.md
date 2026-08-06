# Troubleshooting

_Reference. Symptom-first answers for the common failure modes. Each entry
is: the symptom, the likely cause, and the fix._

## The globe renders black and no tiles appear

- **No imagery layer attached.** Check that the page actually reached the
  globe: `viewer.imageryLayers.length` in the browser console. In
  `Viewer.show()`, an installed wheel uses bundled NaturalEarthII imagery
  when no Ion token or imagery provider is configured. If you passed
  `imagery_provider`, make sure its URL is reachable from the browser (see
  CORS below).
- **CORS blocks the tiles.** Remote imagery servers must send
  `Access-Control-Allow-Origin` headers, or the browser silently drops
  tiles. Test the tile URL directly in the browser; if it loads there but
  not on the globe, it is CORS.

## Tiles load in my browser but not on a headless server or CI

- **The network is blocked or rate-limited.** Tile servers (notably
  OpenStreetMap) block cloud CI IP ranges. For an installed wheel using
  `show()`, omit `imagery_provider` to use bundled NaturalEarthII imagery,
  or point `imagery_provider` at a server you control. See the OSM policy at
  <https://osm.wiki/Blocked>.

## How does offline mode decide between CDN and bundled Cesium?

- `show()` serves the bundled Cesium build whenever it is present. Published
  wheels include it; source checkouts need `python scripts/fetch_cesium.py`.
  The local server also serves NaturalEarthII imagery, so this path works
  without network access unless the viewer config requests remote resources.
- Static HTML export (`to_html()`) and the Jupyter widget always load
  CesiumJS from the CDN, because they have no local server. Vendoring the
  package folder next to a static page does not change those URLs; an offline
  standalone export is not currently supported.

## The Jupyter widget renders nothing

- **Missing extra.** Install `pip install "cesiumkit[widget]"`, then
  restart the kernel. The widget needs `anywidget` and `ipywidgets`.
- **Old notebook.** Hard-restart the kernel (not just "restart & run all")
  after installing so the widget JavaScript reloads.

## `canvas_to_image()` / `screenshot()` fail with a CORS error

- Canvas readback is subject to browser CORS rules: every imagery tile on
  the canvas must come from a server that permits cross-origin reads. This
  is a browser restriction, not a cesiumkit bug. Use imagery servers that
  send permissive CORS headers, or render against the bundled offline
  imagery.
- `canvas_to_image()` additionally needs `pip install "cesiumkit[images]"`.

## `Viewer.show()` opens no browser window

- The server is running but `open_browser` failed (e.g. headless machine).
  Open the printed URL manually. For fully headless use, see the
  [Headless testing](api/testing.md) page and `cesiumkit.testing`.
