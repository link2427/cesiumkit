"""Public API surface checks.

Every public module must declare ``__all__`` (the API audit contract), every
name it lists must actually exist, and every name *defined* in the module must
be listed. Names re-exported at the top level must resolve too.
"""

from __future__ import annotations

import importlib
import pathlib

import pytest

import cesiumkit

PACKAGE_DIR = pathlib.Path(cesiumkit.__file__).resolve().parent

PUBLIC_MODULES = [
    "base",
    "camera",
    "clock",
    "clustering",
    "color",
    "coordinates",
    "czml",
    "datasources",
    "enums",
    "events",
    "gis",
    "globe",
    "imagery",
    "ion",
    "material",
    "math",
    "particle",
    "properties",
    "raster",
    "scene",
    "terrain",
    "testing",
    "utils",
    "viewer",
    "widget",
]

PUBLIC_ENTITY_MODULES = sorted(p.stem for p in (PACKAGE_DIR / "entities").glob("*.py") if not p.name.startswith("_"))


def _public_module_names() -> list[str]:
    return [f"cesiumkit.{m}" for m in PUBLIC_MODULES] + [f"cesiumkit.entities.{m}" for m in PUBLIC_ENTITY_MODULES]


@pytest.mark.parametrize("module_name", _public_module_names())
def test_module_declares_all(module_name: str) -> None:
    mod = importlib.import_module(module_name)
    assert hasattr(mod, "__all__"), f"{module_name} must declare __all__"
    assert mod.__all__, f"{module_name} __all__ must not be empty"
    for name in mod.__all__:
        assert hasattr(mod, name), f"{module_name}.{name} listed in __all__ but missing"
        assert not name.startswith("_"), f"{module_name} __all__ contains private name {name}"


@pytest.mark.parametrize("module_name", _public_module_names())
def test_all_covers_all_defined_names(module_name: str) -> None:
    """Every name defined in the module (classes/functions) must be in __all__."""
    mod = importlib.import_module(module_name)
    defined = {
        name
        for name, obj in vars(mod).items()
        if not name.startswith("_") and getattr(obj, "__module__", None) == mod.__name__
    }
    missing = defined - set(mod.__all__)
    assert not missing, f"{module_name} defines public names not in __all__: {sorted(missing)}"


def test_top_level_all_resolves() -> None:
    for name in cesiumkit.__all__:
        assert hasattr(cesiumkit, name), f"cesiumkit.{name} listed in __all__ but missing"
