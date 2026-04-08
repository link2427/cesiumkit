"""CZML export module for cesiumkit."""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cesiumkit.clock import ClockConfig


class CzmlDocument:
    """Builds a CZML document from cesiumkit entities."""

    def __init__(self, name: str = "cesiumkit", clock: ClockConfig | None = None) -> None:
        self._packets: list[dict] = []
        self.name = name
        self.clock = clock

    def _preamble_packet(self) -> dict:
        pkt: dict[str, Any] = {
            "id": "document",
            "name": self.name,
            "version": "1.0",
        }
        if self.clock:
            pkt["clock"] = self.clock.to_czml()
        return pkt

    def add_packet(self, packet: dict) -> None:
        """Add a raw CZML packet dict."""
        self._packets.append(packet)

    def add_entity(self, entity: Any) -> None:
        """Add a cesiumkit Entity, converting it to a CZML packet."""
        if hasattr(entity, "to_czml_packet"):
            self._packets.append(entity.to_czml_packet())
        else:
            raise TypeError(f"Cannot convert {type(entity)} to CZML packet")

    def to_list(self) -> list[dict]:
        """Return the complete CZML document as a list of packets."""
        return [self._preamble_packet()] + self._packets

    def to_json(self, indent: int = 2) -> str:
        """Return the CZML document as a formatted JSON string."""
        return json.dumps(self.to_list(), indent=indent)

    def save(self, path: str) -> None:
        """Save the CZML document to a file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
