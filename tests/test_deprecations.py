"""Tests for cesiumkit's project-specific deprecation category."""

import pytest

from cesiumkit._deprecations import (
    DEFAULT_REMOVAL,
    CesiumkitDeprecationWarning,
    warn_deprecated,
)


def test_project_deprecations_use_the_project_warning_category() -> None:
    with pytest.warns(CesiumkitDeprecationWarning, match="old_api"):
        warn_deprecated("old_api", alternative="new_api", removal="2.0")


def test_default_removal_targets_the_next_major_release() -> None:
    assert DEFAULT_REMOVAL == "2.0"
    with pytest.warns(CesiumkitDeprecationWarning, match=r"removed in 2\.0"):
        warn_deprecated("old_api")
