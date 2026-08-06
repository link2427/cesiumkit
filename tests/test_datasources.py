"""Tests for cesiumkit.datasources module."""

import pytest
from pydantic import ValidationError

from cesiumkit.color import RED
from cesiumkit.datasources import (
    CustomDataSource,
    CzmlDataSource,
    GeoJsonDataSource,
    KmlDataSource,
)


class TestCzmlDataSource:
    def test_from_url(self):
        ds = CzmlDataSource(url="https://example.com/data.czml")
        js = ds.to_js()
        assert "CzmlDataSource.load" in js
        assert "example.com/data.czml" in js

    def test_from_data(self):
        data = [{"id": "document", "version": "1.0"}]
        ds = CzmlDataSource(data=data)
        js = ds.to_js()
        assert "CzmlDataSource.load" in js
        assert "document" in js

    def test_source_uri_name_and_visibility_are_applied(self):
        js = CzmlDataSource(
            data=[{"id": "document", "version": "1.0"}],
            source_uri="https://example.com/base/",
            name="Tracked feed",
            show=False,
        ).to_js()
        assert "sourceUri" in js
        assert 'dataSource.name = "Tracked feed"' in js
        assert "dataSource.show = false" in js

    @pytest.mark.parametrize("kwargs", [{}, {"url": "a.czml", "data": []}, {"url": ""}])
    def test_requires_exactly_one_valid_source(self, kwargs):
        with pytest.raises(ValidationError):
            CzmlDataSource(**kwargs)


class TestGeoJsonDataSource:
    def test_from_url(self):
        ds = GeoJsonDataSource(url="https://example.com/data.geojson")
        js = ds.to_js()
        assert "GeoJsonDataSource.load" in js
        assert "example.com/data.geojson" in js

    def test_with_options(self):
        ds = GeoJsonDataSource(
            url="https://example.com/data.geojson",
            clamp_to_ground=True,
            stroke=RED,
            stroke_width=3,
        )
        js = ds.to_js()
        assert "clampToGround: true" in js
        assert "strokeWidth: 3" in js

    def test_source_uri_and_common_options_are_applied(self):
        js = GeoJsonDataSource(
            data={"type": "FeatureCollection", "features": []},
            source_uri="https://example.com/base/",
            name="Boundaries",
            show=False,
        ).to_js()
        assert "sourceUri" in js
        assert 'dataSource.name = "Boundaries"' in js
        assert "dataSource.show = false" in js

    @pytest.mark.parametrize("kwargs", [{}, {"url": "a.geojson", "data": {}}, {"url": ""}])
    def test_requires_exactly_one_valid_source(self, kwargs):
        with pytest.raises(ValidationError):
            GeoJsonDataSource(**kwargs)


class TestKmlDataSource:
    def test_from_url(self):
        ds = KmlDataSource(url="https://example.com/data.kml")
        js = ds.to_js()
        assert "KmlDataSource.load" in js
        assert "example.com/data.kml" in js

    def test_url_required(self):
        with pytest.raises(ValidationError):
            KmlDataSource()

    def test_empty_url_is_rejected_and_source_uri_is_forwarded(self):
        with pytest.raises(ValidationError):
            KmlDataSource(url="")
        assert "sourceUri" in KmlDataSource(url="doc.kml", source_uri="https://example.com/base/").to_js()


class TestCustomDataSource:
    def test_with_name(self):
        ds = CustomDataSource(name="MyData")
        js = ds.to_js()
        assert "CustomDataSource" in js
        assert "MyData" in js

    def test_without_name(self):
        ds = CustomDataSource()
        js = ds.to_js()
        assert "CustomDataSource()" in js

    def test_hidden_data_source_is_hidden(self):
        assert "dataSource.show = false" in CustomDataSource(show=False).to_js()
