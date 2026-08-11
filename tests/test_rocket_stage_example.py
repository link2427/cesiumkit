"""Tests for the rocket stage-separation example."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_example():
    path = Path(__file__).parents[1] / "examples" / "12_rocket_stage_separation.py"
    spec = importlib.util.spec_from_file_location("rocket_stage_example", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_second_stage_inherits_separation_position_and_velocity() -> None:
    example = _load_example()
    booster, second_stage = example.build_trajectories()

    separation_state = next(state for state in booster if state.elapsed_seconds == example.SEPARATION_SECONDS)
    second_stage_initial_state = second_stage[0]

    assert second_stage_initial_state == separation_state
    assert second_stage_initial_state is not separation_state
    assert second_stage_initial_state.downrange_velocity_mps == 240
    assert second_stage_initial_state.vertical_velocity_mps == 1800


def test_second_stage_diverges_after_separation() -> None:
    example = _load_example()
    booster, second_stage = example.build_trajectories()

    booster_after_separation = next(
        state for state in booster if state.elapsed_seconds == example.SEPARATION_SECONDS + example.TIME_STEP_SECONDS
    )
    second_stage_after_separation = second_stage[1]

    assert second_stage_after_separation.downrange_m > booster_after_separation.downrange_m
    assert second_stage_after_separation.altitude_m > booster_after_separation.altitude_m


def test_example_builds_two_time_dynamic_entities() -> None:
    example = _load_example()
    viewer = example.build_viewer()
    html = viewer.to_html()

    assert viewer.entity_count == 2
    assert 'id: "first-stage"' in html
    assert 'id: "second-stage"' in html
    assert html.count("new Cesium.SampledPositionProperty()") == 2
    assert "2026-01-01T00:02:00Z" in html
