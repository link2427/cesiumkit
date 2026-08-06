"""Tests for package release metadata."""

import re
from importlib.metadata import requires
from pathlib import Path

import cesiumkit


def test_runtime_version_matches_project_metadata():
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    match = re.search(r'^version = "([^"]+)"$', pyproject.read_text(), re.MULTILINE)
    assert match is not None
    assert cesiumkit.__version__ == match.group(1)


def test_datashader_extra_is_functionally_complete():
    metadata_requirements = requires("cesiumkit") or []
    dependency_names = {
        re.split(r"[<>=!~[]", requirement, maxsplit=1)[0].lower()
        for requirement in metadata_requirements
        if re.search(r"extra\s*==\s*['\"]datashader['\"]", requirement)
    }
    assert {
        "datashader",
        "geopandas",
        "pillow",
        "rio-tiler",
        "rasterio",
        "shapely",
        "xarray",
    } <= dependency_names
