"""Deprecation helpers for the public API.

Policy (see CONTRIBUTING): deprecate in a minor release, remove only in
1.0. Every warning names the release that removes the feature and the
replacement when one exists, so callers always know what to migrate to.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

_F = TypeVar("_F", bound=Callable[..., Any])

DEFAULT_REMOVAL = "1.0"


def _format_message(what: str, alternative: str | None, removal: str) -> str:
    msg = f"{what} is deprecated and will be removed in {removal}."
    if alternative:
        msg += f" Use {alternative} instead."
    return msg


def warn_deprecated(
    what: str,
    *,
    alternative: str | None = None,
    removal: str = DEFAULT_REMOVAL,
) -> None:
    """Emit a DeprecationWarning naming the removal release.

    Args:
        what: The deprecated thing, e.g. ``Viewer(cesium_version=...)``.
        alternative: What to use instead, e.g. ``show(cesium_version=...)``.
        removal: The release that removes the feature (default "1.0").
    """
    warnings.warn(
        _format_message(what, alternative, removal),
        DeprecationWarning,
        stacklevel=2,
    )


def deprecated(
    *,
    alternative: str | None = None,
    removal: str = DEFAULT_REMOVAL,
) -> Callable[[_F], _F]:
    """Decorator that warns when the decorated callable is used.

    Use this for functions and methods. For constructor parameters or
    attribute-level warts, call :func:`warn_deprecated` at the use site
    instead.
    """

    def decorate(obj: _F) -> _F:
        name = obj.__qualname__

        @wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn_deprecated(name, alternative=alternative, removal=removal)
            return obj(*args, **kwargs)

        return cast(_F, wrapper)

    return decorate
