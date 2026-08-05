# Migration guide: 0.x to 1.0

_Reference. Everything that changes between the current 0.x series and
1.0, with before/after code. If you upgrade straight to 1.0, run through
this list; if you stay on 0.x, the deprecated items still work (with a
warning) until 1.0._

## The 1.0 contract

From 1.0 on, cesiumkit follows semantic versioning strictly: breaking
changes only land in major releases, and any deprecation is announced at
least one minor release before removal. APIs deprecated in 0.8 are removed
at 1.0.

## Removed at 1.0

These were deprecated in 0.8.0 and are removed in 1.0.0. Both still work
in 0.9 with a `DeprecationWarning`; in 1.0 they are gone and the
alternatives below are the supported paths.

### 1. `Viewer(cesium_version=...)`

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

### 2. `OpenStreetMapImageryProvider`

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
python -W error::DeprecationWarning your_script.py
```

Any use of a deprecated API fails loudly instead of silently degrading.
The changelog `Deprecated` sections list every item and its removal
release.
