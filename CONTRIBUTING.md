# Contributing to cesiumkit

Thanks for your interest in contributing! This guide will get you set up and explain how the codebase works.

## Development setup

```bash
# Clone the repo
git clone https://github.com/jacobs-github/cesiumkit.git
cd cesiumkit

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cesiumkit

# Run a specific test file
pytest tests/test_viewer.py
```

All 143+ tests should pass. Please ensure tests pass before submitting a PR.

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
- Keep `__init__.py` exports alphabetically sorted by class name.

## Submitting a PR

1. Fork the repo and create a branch from `main`.
2. Make your changes and add/update tests.
3. Run `pytest` and make sure all tests pass.
4. Write a clear PR description explaining what changed and why.
5. Submit!
