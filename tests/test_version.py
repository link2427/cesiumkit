"""Tests for package release metadata."""

import re
from pathlib import Path

import cesiumkit


def test_runtime_version_matches_project_metadata():
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    match = re.search(r'^version = "([^"]+)"$', pyproject.read_text(), re.MULTILINE)
    assert match is not None
    assert cesiumkit.__version__ == match.group(1)
