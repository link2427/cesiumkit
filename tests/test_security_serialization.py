"""Security regressions for HTML rendering and JavaScript serialization."""

import pytest

import cesiumkit
from cesiumkit._html import HtmlDocument
from cesiumkit._js_serializer import to_js_options, to_js_value
from cesiumkit._template import get_template_env


def test_html_templates_enable_autoescape_by_default() -> None:
    assert get_template_env().autoescape is True


def test_mapping_keys_are_preserved_without_camelization() -> None:
    value = {
        "snake_case": {"nested_key": "value"},
        "__proto__": "must remain data",
        "<hostile-key>": "value",
    }

    result = to_js_value(value)

    assert '["snake_case"]' in result
    assert '["nested_key"]' in result
    assert '["__proto__"]' in result
    assert '["\\u003chostile-key\\u003e"]' in result
    assert "snakeCase" not in result
    assert "nestedKey" not in result


def test_only_option_field_keys_are_camelized() -> None:
    result = to_js_options({"pixel_size": 10, "metadata": {"source_name": "raw"}})

    assert "pixelSize: 10" in result
    assert '["source_name"]' in result
    assert "sourceName" not in result


def test_inline_script_serializer_escapes_script_breakout_and_line_separators() -> None:
    result = to_js_value("</script>\u2028\u2029")

    assert "</script>" not in result
    assert "\u2028" not in result
    assert "\u2029" not in result
    assert "\\u003c/script\\u003e" in result
    assert "\\u2028" in result
    assert "\\u2029" in result


def test_geojson_payload_keys_are_not_camelized() -> None:
    source = cesiumkit.GeoJsonDataSource(
        data={
            "type": "FeatureCollection",
            "features": [{"properties": {"building_height": 12, "__proto__": "data"}}],
        }
    )

    result = source.to_js()

    assert '["building_height"]' in result
    assert '["__proto__"]' in result
    assert "buildingHeight" not in result


def test_html_contexts_are_escaped_or_serialized() -> None:
    document = HtmlDocument(
        cesium_base_url='https://cdn.example/" onerror="window.bad=1',
        ion_token="</script><script>window.tokenBad=1</script>",
        title="</title><script>window.titleBad=1</script>",
        container_id='map"><script>window.idBad=1</script>',
        width="100%; </style><script>window.widthBad=1</script>",
        height="100%; </style><script>window.heightBad=1</script>",
    )

    result = document.render()

    assert "window.titleBad=1</script>" not in result
    assert "window.idBad=1</script>" not in result
    assert "window.tokenBad=1</script>" not in result
    assert "window.widthBad=1</script>" not in result
    assert "window.heightBad=1</script>" not in result
    assert "&lt;/title&gt;" in result
    assert "&#34; onerror=&#34;" in result
    assert 'container.style.width = "100%; \\u003c/style\\u003e' in result
    assert 'container.style.height = "100%; \\u003c/style\\u003e' in result


def test_executable_cesium_base_urls_are_rejected() -> None:
    with pytest.raises(ValueError, match="relative, HTTP, or HTTPS"):
        HtmlDocument(cesium_base_url="javascript:alert(1)").render()


def test_jupyter_iframe_attributes_and_srcdoc_are_escaped() -> None:
    result = HtmlDocument().render_jupyter(
        "<script>window.srcdocBad=1</script>",
        width='100%" onload="window.widthBad=1',
        height='600" onload="window.heightBad=1',
    )

    assert "<script>window.srcdocBad=1</script>" not in result
    assert "&lt;script&gt;window.srcdocBad=1&lt;/script&gt;" in result
    assert 'width="100%&#34; onload=&#34;window.widthBad=1"' in result
    assert 'height="600&#34; onload=&#34;window.heightBad=1"' in result


def test_hostile_infobox_description_cannot_remove_its_sandbox() -> None:
    viewer = cesiumkit.Viewer()
    viewer.add_entity(cesiumkit.Entity(description="<script>parent.__cesiumkitCompromised = true</script>"))

    result = viewer.to_html()

    assert "removeAttribute('sandbox')" not in result
    assert 'removeAttribute("sandbox")' not in result
    assert "frame.src = 'about:blank'" not in result
    assert 'frame.src = "about:blank"' not in result
    assert "<script>parent.__cesiumkitCompromised" not in result
    assert "\\u003cscript\\u003eparent.__cesiumkitCompromised" in result


def test_hostile_infobox_description_cannot_access_parent_context(playwright_browser) -> None:
    from cesiumkit._vendor import vendor_dir

    if vendor_dir() is None:
        pytest.skip("bundled Cesium build not present")

    from cesiumkit.testing import serve

    viewer = cesiumkit.Viewer()
    viewer.add_entity(cesiumkit.Entity(description="<script>parent.__cesiumkitCompromised = true</script>"))
    with serve(viewer) as url:
        page = playwright_browser.new_page()
        try:
            page.goto(url, wait_until="load")
            page.evaluate("() => { window.viewer.selectedEntity = window.viewer.entities.values[0]; }")
            page.wait_for_timeout(500)
            assert page.evaluate("() => window.__cesiumkitCompromised === true") is False
        finally:
            page.close()


def test_runtime_bridge_is_opt_in_and_carries_the_session_token() -> None:
    document = HtmlDocument()

    static_html = document.render()
    runtime_html = document.render(
        render_runtime_bridge=True,
        session_token="session-\u2028</script><script>window.bridgeBad=1</script>",
    )

    assert "/__cesiumkit_cmd" not in static_html
    assert "/__cesiumkit_result" not in static_html
    assert "__cesiumkitPostResult" not in static_html
    assert "const __cesiumkitSessionToken" in runtime_html
    assert "token: __cesiumkitSessionToken" in runtime_html
    assert "URLSearchParams" in runtime_html
    assert "window.bridgeBad=1</script>" not in runtime_html
    assert "\\u2028\\u003c/script\\u003e" in runtime_html


def test_runtime_bridge_requires_a_session_token() -> None:
    with pytest.raises(ValueError, match="session_token"):
        HtmlDocument().render(render_runtime_bridge=True)
