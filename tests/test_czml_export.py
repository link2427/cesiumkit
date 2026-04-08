"""Tests for CZML export functionality."""

import json

import cesiumkit
from cesiumkit.czml import CzmlDocument


class TestCzmlDocument:
    def test_preamble(self):
        doc = CzmlDocument(name="Test")
        packets = doc.to_list()
        assert len(packets) == 1
        assert packets[0]["id"] == "document"
        assert packets[0]["name"] == "Test"
        assert packets[0]["version"] == "1.0"

    def test_add_entity(self):
        doc = CzmlDocument()
        doc.add_entity(
            cesiumkit.Entity(
                id="e1",
                name="Entity 1",
                position=cesiumkit.Cartesian3.from_degrees(-75, 40, 100),
            )
        )
        packets = doc.to_list()
        assert len(packets) == 2
        assert packets[1]["id"] == "e1"
        assert packets[1]["name"] == "Entity 1"

    def test_to_json(self):
        doc = CzmlDocument()
        doc.add_entity(cesiumkit.Entity(id="e1", name="E1"))
        json_str = doc.to_json()
        parsed = json.loads(json_str)
        assert len(parsed) == 2

    def test_save(self, tmp_path):
        doc = CzmlDocument()
        doc.add_entity(cesiumkit.Entity(id="e1", name="E1"))
        path = tmp_path / "test.czml"
        doc.save(str(path))
        content = json.loads(path.read_text())
        assert content[0]["id"] == "document"

    def test_with_clock(self):
        clock = cesiumkit.ClockConfig(
            start_time=cesiumkit.JulianDate.from_iso8601("2024-01-01T00:00:00Z"),
            stop_time=cesiumkit.JulianDate.from_iso8601("2024-01-02T00:00:00Z"),
            multiplier=60,
        )
        doc = CzmlDocument(name="Animated", clock=clock)
        packets = doc.to_list()
        assert "clock" in packets[0]
        assert packets[0]["clock"]["multiplier"] == 60

    def test_add_raw_packet(self):
        doc = CzmlDocument()
        doc.add_packet({"id": "custom", "name": "Custom"})
        packets = doc.to_list()
        assert len(packets) == 2
        assert packets[1]["id"] == "custom"
