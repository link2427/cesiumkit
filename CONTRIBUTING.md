# Contributing to cesiumkit

Thanks for your interest in contributing! This guide will get you set up and explain how the codebase works.

## Development setup

```bash
# Clone the repo
git clone https://github.com/link2427/cesiumkit.git
cd cesiumkit

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Running tests

```bash
# Run the core test suite (tests for unavailable optional features are skipped)
pytest

# Run with coverage
pytest --cov=cesiumkit

# Run a specific test file
pytest tests/test_viewer.py
```

To run the complete suite, install every feature used by the tests and the
Playwright browser:

```bash
pip install -e ".[dev,gis,raster,datashader,images,testing,widget]"
python -m playwright install chromium
pytest
```

All tests should pass. Please ensure the relevant tests pass before submitting
a PR.

## Project structure

```
cesiumkit/
  __init__.py          # Public API -- re-exports everything
  base.py              # CesiumBase (Pydantic root) and CesiumEnum
  _js_serializer.py    # Python-to-JavaScript value serialization
  _template.py         # Jinja2 template loading
  _html.py             # HTML generation
  viewer.py            # Viewer class (main entry point)
  color.py             # Color with 148 named constants
  coordinates.py       # Cartesian2, Cartesian3, Cartographic, etc.
  enums.py             # All CesiumJS enums
  material.py          # Material types (Stripe, Glow, etc.)
  properties.py        # Time-dynamic properties
  camera.py            # Camera operations
  clock.py             # JulianDate, ClockConfig
  imagery.py           # Imagery providers
  terrain.py           # Terrain providers
  datasources.py       # GeoJSON, CZML, KML data sources
  czml.py              # CZML document export
  events.py            # ScreenSpaceEventHandler
  ion.py               # Cesium Ion integration
  scene.py             # Scene configuration
  globe.py             # Globe configuration
  entities/
    _base.py           # Entity, EntityGraphics base
    point.py           # PointGraphics
    polygon.py         # PolygonGraphics
    ...                # One file per entity type
  templates/
    viewer.html.j2     # Jinja2 HTML template
tests/
  test_viewer.py
  test_entities.py
  ...
examples/
  01_basic_point.py
  ...
```

## Architecture

### The `to_js()` pattern

Every class that maps to a CesiumJS object has a `to_js()` method that returns a JavaScript expression string. This is the core serialization mechanism:

```python
class Cartesian3(CesiumBase):
    x: float
    y: float
    z: float

    def to_js(self) -> str:
        return f"new Cesium.Cartesian3({self.x}, {self.y}, {self.z})"
```

Composability comes from calling `to_js()` recursively -- a PolygonGraphics calls `to_js()` on its positions, materials, etc.

### CesiumBase

All models inherit from `CesiumBase(pydantic.BaseModel)`. It provides:
- `_js_class_name()` -- the Cesium constructor name (e.g., `"Cesium.Cartesian3"`)
- `_js_fields()` -- dict of field names to JS values, using `to_js_value()` from `_js_serializer.py`
- Default `to_js()` -- `new {class_name}({options})` using `to_js_options()`

### EntityGraphics

Entity graphics types (PointGraphics, PolygonGraphics, etc.) inherit from `EntityGraphics` which serializes as a plain JS object literal `{ pixelSize: 12, color: ... }` rather than `new Cesium.PointGraphics(...)` because CesiumJS's Entity constructor expects option objects.

### CesiumEnum

Enums inherit from `CesiumEnum(str, Enum)` and serialize as `Cesium.EnumType.VALUE` via `to_js()`. The `str` base class is required for Pydantic compatibility.

**Important:** In `_js_serializer.py`, the Enum isinstance check must come before the str check, because CesiumEnum inherits from str.

### Viewer

The Viewer class is a plain Python class (not Pydantic) because it manages mutable state -- entity lists, camera operations, event handlers, scripts. It uses the Jinja2 template to render the final HTML.

## Adding a new entity type

1. Create `cesiumkit/entities/my_type.py`:

```python
from cesiumkit.entities._base import EntityGraphics


class MyTypeGraphics(EntityGraphics):
    """Cesium MyType graphics."""

    some_field: float = 1.0
    # ... fields matching CesiumJS constructor options

    def _js_class_name(self) -> str:
        return "Cesium.MyTypeGraphics"
```

2. Add the field to `Entity` in `cesiumkit/entities/_base.py`:

```python
my_type: MyTypeGraphics | None = None
```

3. Re-export from `cesiumkit/entities/__init__.py` and `cesiumkit/__init__.py`.

4. Add CZML support in the Entity's `to_czml_packet()` method if applicable.

5. Write tests in `tests/test_entities.py`.

6. Add an example usage to the relevant example file or create a new one.

## Code conventions

- **Pydantic v2** models for all data classes. Use `model_validator`, `field_validator` when needed.
- **Snake case** for Python fields, auto-converted to camelCase for JavaScript via `camelize()`.
- **Type hints** on all public methods.
- Field defaults should match CesiumJS defaults where possible.
- Declare public exports explicitly in `__all__`. Preserve the established
  export order unless an intentional API-contract change updates its tests.

## Submitting a PR

1. Fork the repo and create a branch from `main`.
2. Make your changes and add/update tests.
3. Run `pytest` and make sure all tests pass.
4. Write a clear PR description explaining what changed and why.
5. Submit!

## Deprecation policy

cesiumkit follows the pandas-style schedule: **deprecate in a minor
release, remove in a later one**, with at least one minor of notice.

### Pre-1.0 (0.x)

Before 1.0 the API is still settling, so the window is shorter:
deprecations land in a minor and removal happens at the next minor that
announces it, or at 1.0 for items deprecated in 0.8. The 0.x era is the
only time removals are allowed on this cadence.

- To deprecate an API, emit `CesiumkitDeprecationWarning` via
  `cesiumkit._deprecations` (`warn_deprecated` for constructor params and
  attributes, the `@deprecated` decorator for functions/methods). Every
  message names the removal release and the replacement when one exists.
- Do **not** remove deprecated APIs in a minor release. Removal happens at
  1.0 (or the next major) and is listed in the changelog `Removed`
  section.
- Every release that adds deprecations gets a changelog `Deprecated`
  section listing each item, its replacement, and its removal release.
- The `deprecations` CI job treats only
  `CesiumkitDeprecationWarning` as an error, so internal uses of deprecated
  APIs and regressions fail without promoting valid dependency warnings to
  release blockers. Tests that intentionally exercise a deprecated API must
  wrap the call in `pytest.warns(CesiumkitDeprecationWarning)`.

### From 1.0 on

1.0 makes the public API a compatibility contract. Additions require an
intentional compatibility review; compatible additions may ship in a minor
release. After it:

- **Breaking changes require a major version bump.** The exported surface
  (everything in a module's `__all__`, constructor signatures, and
  documented behavior) is a contract. Removing or changing it is a major
  release, full stop.
- **Deprecations are announced at least one minor before removal.** An API
  deprecated in `1.x` is not removed before `2.0`, and `2.0` must carry
  the removal notes from every deprecation made during 1.x.
- The changelog keeps its `Deprecated` / `Removed` sections on every
  release that touches either.
- The project-specific deprecation CI gate stays on forever: a green suite
  is the proof that nothing internal uses a deprecated path.

## Version support

cesiumkit supports the Python versions declared by `requires-python` in
`pyproject.toml` and exercised in CI, currently Python 3.10 through 3.14. The
project uses [SPEC 0](https://scientific-python.org/specs/spec-0000/) as guidance
when deciding when it is reasonable to raise the minimum, but may retain older
versions while dependencies and CI remain healthy.

- `requires-python`, classifiers, documentation, and the CI test matrix must
  remain in sync.
- A Python floor or dependency-minimum change is never made in a patch release
  and must be called out in the changelog.

## Releasing

Releases are cut from `main` with an annotated tag (`vX.Y.Z`, matching the
`version` in `pyproject.toml`):

1. Bump the version in `pyproject.toml` and `cesiumkit/_version.py`, add a
   dated `## [X.Y.Z]` entry to `CHANGELOG.md` (Keep a Changelog format), and
   merge that as a normal PR.
2. After that PR is merged, update local `main`, create the annotated tag, and
   push it:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a vX.Y.Z -m "cesiumkit vX.Y.Z"
   git push origin vX.Y.Z
   ```

3. Create the release from that existing tag with
   `gh release create vX.Y.Z --verify-tag --title "cesiumkit vX.Y.Z"`. The
   release notes summarize what changed; the last line must link the changelog,
   e.g. `Full changelog: https://github.com/link2427/cesiumkit/blob/main/CHANGELOG.md`.
4. Before the first release, configure trusted publishers for both the
   `testpypi` and `pypi` GitHub environments. Require approval for the `pypi`
   environment; it is the final production gate. Also enable GitHub private
   vulnerability reporting so the reporting path in `SECURITY.md` is active.
5. The release event runs `Publish to PyPI` and `Gallery` automatically. The
   publish workflow fetches checksum-verified Cesium, builds wheel and sdist
   **once**, browser-smokes the installed wheel with the vendored build, then
   uploads those exact artifacts to TestPyPI. TestPyPI's published digests and
   a browser smoke test must pass before the `pypi` environment can promote
   the same GitHub artifact.
6. Re-runs use PyPI's immutable-file behavior safely: existing files are
   skipped only after their published SHA-256 values match the staged files.
   A digest mismatch stops the run; do not retag or reuse a version.
   A manual workflow run requires an existing annotated `vX.Y.Z` tag and
   refuses a branch or a tag whose version differs from `pyproject.toml`.
7. Verify: the publish run succeeds and `https://pypi.org/project/cesiumkit/`
   shows the new version; the gallery run finishes and its screenshots are
   committed to `gallery-images`; the follow-up docs run publishes them.
