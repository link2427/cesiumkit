# Migration guide: 0.x to 1.0

_Reference. Everything that changes between the current 0.x series and
1.0, with before/after code. If you upgrade straight to 1.0, run through
this list. The two APIs deprecated in 0.8 warn until they are removed in
1.0; compatibility paths first deprecated in 1.0 remain available through
1.x._

## The 1.0 contract

From 1.0 on, cesiumkit follows semantic versioning strictly: breaking
changes only land in major releases, and any deprecation is announced at
least one minor release before removal. The APIs deprecated in 0.8 were
removed at 1.0 — that was the last time removals happened on that short a
schedule; see the deprecation policy in CONTRIBUTING.md for the 1.x rules.

## Removed at 1.0

These APIs were deprecated in 0.8.0 and still work in 0.9 with a
`CesiumkitDeprecationWarning`. They are the only 0.x APIs removed in 1.0.

### `Viewer(cesium_version=...)`

The argument overrode the bundled, pinned CesiumJS build with an arbitrary
CDN version, which could break against the generated JavaScript.

Before:

```python
viewer = cesiumkit.Viewer(cesium_version="1.115")
```

After (drop the argument):

```python
viewer = cesiumkit.Viewer()  # uses the bundled Cesium build
```

### `OpenStreetMapImageryProvider`

CesiumJS itself deprecates the provider in favor of URL-template providers.

Before:

```python
viewer = cesiumkit.Viewer(imagery_provider=cesiumkit.OpenStreetMapImageryProvider())
```

After:

```python
viewer = cesiumkit.Viewer(
    imagery_provider=cesiumkit.UrlTemplateImageryProvider(
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        maximum_level=19,
    )
)
```

## Deprecated in 1.0 and supported through 1.x

These compatibility paths emit `CesiumkitDeprecationWarning` in 1.0 and are
scheduled for removal in 2.0.

### `CesiumKitWidget(cesium_version=...)`

The widget still accepts a strictly validated Cesium version override for 0.x
compatibility. It warns because generated JavaScript is tested only against
Cesium 1.144. Omit the override for the supported path.

Before:

```python
from cesiumkit.widget import CesiumKitWidget

widget = CesiumKitWidget(viewer, cesium_version="1.115")
```

After:

```python
widget = viewer.to_widget()
```

### `Cesium3DTileset.maximum_memory_usage`

Cesium 1.144 no longer recognizes `maximumMemoryUsage`. The compatibility
field now converts its MiB value to Cesium's `cacheBytes`; new code should use
`cache_bytes` directly, measured in bytes.

Before:

```python
tileset = cesiumkit.Cesium3DTileset(
    url="https://example.com/tileset.json",
    maximum_memory_usage=512,
)
```

After:

```python
tileset = cesiumkit.Cesium3DTileset(
    url="https://example.com/tileset.json",
    cache_bytes=512 * 1024 * 1024,
)
```

### Raw strings in `CallbackProperty`

Raw JavaScript strings are still inserted verbatim for 0.x compatibility but
now warn. Use `JsCode` so executable input is explicit:

```python
# Deprecated; accepted through 1.x
callback = cesiumkit.CallbackProperty(callback="function() { return 1; }")

# Supported
callback = cesiumkit.CallbackProperty(callback=cesiumkit.JsCode("function() { return 1; }"))
```

## Already changed in 0.x (nothing to do, but worth knowing)

- **`BingMapsImageryProvider.key` and `KmlDataSource.url` are required**
  (0.6): the old `""` defaults produced providers that always failed.
- **The Jupyter widget applies viewer state** (0.6): viewer options, data
  sources, camera operations, and scene/globe/clock config now actually
  load in the widget.
- **The package is typed** (0.7): a `py.typed` marker ships in the wheel
  and the public API is pyright-clean; type checkers can now validate your
  code against cesiumkit.

## How to check what will break

```bash
python -W error::cesiumkit._deprecations.CesiumkitDeprecationWarning your_script.py
```

Any use of a deprecated API fails loudly instead of silently degrading.
The changelog `Deprecated` sections list every item and its removal
release.
