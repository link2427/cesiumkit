"""Jinja2 template environment for cesiumkit."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import jinja2

from cesiumkit._js_serializer import to_js_value


def _tojs_filter(obj) -> str:
    """Jinja2 filter that converts Python values to JavaScript expressions."""
    return to_js_value(obj)


def get_template_env() -> jinja2.Environment:
    """Create and return the Jinja2 environment for cesiumkit templates."""
    template_dir = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    env.filters["tojs"] = _tojs_filter
    return env


def render_template(template_name: str, **kwargs) -> str:
    """Render a template with the given context."""
    env = get_template_env()
    template = env.get_template(template_name)
    return template.render(**kwargs)
