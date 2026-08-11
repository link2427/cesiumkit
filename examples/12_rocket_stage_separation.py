"""Rocket staging: Hand position and velocity to a separating second stage."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from math import cos, radians

import cesiumkit

LAUNCH_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
LAUNCH_LONGITUDE = -80.6480
LAUNCH_LATITUDE = 28.5721
SEPARATION_SECONDS = 120
END_SECONDS = 480
TIME_STEP_SECONDS = 10


@dataclass(frozen=True)
class FlightState:
    """A simple local position-and-velocity state used by this example."""

    elapsed_seconds: float
    downrange_m: float
    altitude_m: float
    downrange_velocity_mps: float
    vertical_velocity_mps: float


def advance_state(
    state: FlightState,
    duration_s: float,
    *,
    downrange_acceleration_mps2: float,
    vertical_acceleration_mps2: float,
) -> FlightState:
    """Advance a state with constant acceleration."""
    return FlightState(
        elapsed_seconds=state.elapsed_seconds + duration_s,
        downrange_m=(
            state.downrange_m
            + state.downrange_velocity_mps * duration_s
            + 0.5 * downrange_acceleration_mps2 * duration_s**2
        ),
        altitude_m=(
            state.altitude_m
            + state.vertical_velocity_mps * duration_s
            + 0.5 * vertical_acceleration_mps2 * duration_s**2
        ),
        downrange_velocity_mps=state.downrange_velocity_mps + downrange_acceleration_mps2 * duration_s,
        vertical_velocity_mps=state.vertical_velocity_mps + vertical_acceleration_mps2 * duration_s,
    )


def propagate(
    initial_state: FlightState,
    stop_time_s: float,
    *,
    downrange_acceleration_mps2: float,
    vertical_acceleration_mps2: float,
) -> list[FlightState]:
    """Return regularly sampled states through ``stop_time_s``."""
    states = [initial_state]
    while states[-1].elapsed_seconds < stop_time_s:
        duration_s = min(TIME_STEP_SECONDS, stop_time_s - states[-1].elapsed_seconds)
        states.append(
            advance_state(
                states[-1],
                duration_s,
                downrange_acceleration_mps2=downrange_acceleration_mps2,
                vertical_acceleration_mps2=vertical_acceleration_mps2,
            )
        )
    return states


def build_trajectories() -> tuple[list[FlightState], list[FlightState]]:
    """Build booster and second-stage trajectories with a shared separation state."""
    launch_state = FlightState(0, 0, 0, 0, 0)
    joined_ascent = propagate(
        launch_state,
        SEPARATION_SECONDS,
        downrange_acceleration_mps2=2.0,
        vertical_acceleration_mps2=15.0,
    )

    separation_state = joined_ascent[-1]

    # The second stage starts with a copy of the booster's position and velocity.
    second_stage_initial_state = replace(separation_state)

    booster_after_separation = propagate(
        separation_state,
        END_SECONDS,
        downrange_acceleration_mps2=0.0,
        vertical_acceleration_mps2=-9.81,
    )
    second_stage = propagate(
        second_stage_initial_state,
        END_SECONDS,
        downrange_acceleration_mps2=10.0,
        vertical_acceleration_mps2=5.0,
    )

    # Avoid adding the separation sample twice to the booster's trajectory.
    booster = joined_ascent + booster_after_separation[1:]
    return booster, second_stage


def state_time(state: FlightState) -> str:
    """Convert elapsed simulation time to an ISO-8601 timestamp."""
    value = LAUNCH_TIME + timedelta(seconds=state.elapsed_seconds)
    return value.isoformat().replace("+00:00", "Z")


def state_position(state: FlightState) -> cesiumkit.Cartesian3:
    """Convert the local demonstration state to a Cesium globe position."""
    meters_per_degree_longitude = 111_320 * cos(radians(LAUNCH_LATITUDE))
    longitude = LAUNCH_LONGITUDE + state.downrange_m / meters_per_degree_longitude
    return cesiumkit.Cartesian3.from_degrees(longitude, LAUNCH_LATITUDE, max(0.0, state.altitude_m))


def sampled_position(states: list[FlightState]) -> cesiumkit.SampledPositionProperty:
    """Convert flight states to a time-dynamic Cesium position."""
    position = cesiumkit.SampledPositionProperty(interpolation_algorithm="LINEAR")
    for state in states:
        position.add_sample(state_time(state), state_position(state))
    return position


def build_viewer() -> cesiumkit.Viewer:
    """Create the animated two-stage launch viewer."""
    booster_states, second_stage_states = build_trajectories()
    separation_state = second_stage_states[0]

    viewer = cesiumkit.Viewer(
        title="Rocket Stage Separation",
        should_animate=True,
        clock=cesiumkit.ClockConfig(
            start_time=cesiumkit.JulianDate.from_datetime(LAUNCH_TIME),
            stop_time=cesiumkit.JulianDate.from_datetime(LAUNCH_TIME + timedelta(seconds=END_SECONDS)),
            current_time=cesiumkit.JulianDate.from_datetime(LAUNCH_TIME),
            clock_range=cesiumkit.ClockRange.LOOP_STOP,
            multiplier=50,
        ),
    )

    viewer.add_entity(
        cesiumkit.Entity(
            id="first-stage",
            name="First stage",
            description="<p>The booster coasts under gravity after stage separation.</p>",
            position=sampled_position(booster_states),
            point=cesiumkit.PointGraphics(
                pixel_size=11,
                color=cesiumkit.Color.ORANGE,
                outline_color=cesiumkit.Color.WHITE,
                outline_width=2,
            ),
            label=cesiumkit.LabelGraphics(
                text="First stage",
                fill_color=cesiumkit.Color.ORANGE,
                pixel_offset=cesiumkit.Cartesian2(x=12, y=0),
                horizontal_origin=cesiumkit.HorizontalOrigin.LEFT,
            ),
            path=cesiumkit.PathGraphics(
                width=3,
                lead_time=0,
                trail_time=END_SECONDS,
                material=cesiumkit.PolylineGlowMaterial(color=cesiumkit.Color.ORANGE, glow_power=0.15),
            ),
        )
    )

    viewer.add_entity(
        cesiumkit.Entity(
            id="second-stage",
            name="Second stage",
            description=(
                "<p>Starts at separation with the first stage's position and velocity: "
                f"{separation_state.downrange_velocity_mps:.0f} m/s downrange and "
                f"{separation_state.vertical_velocity_mps:.0f} m/s vertical.</p>"
            ),
            # Its first sample is at separation, so it is not drawn before deployment.
            position=sampled_position(second_stage_states),
            point=cesiumkit.PointGraphics(
                pixel_size=11,
                color=cesiumkit.Color.CYAN,
                outline_color=cesiumkit.Color.WHITE,
                outline_width=2,
            ),
            label=cesiumkit.LabelGraphics(
                text="Second stage",
                fill_color=cesiumkit.Color.CYAN,
                pixel_offset=cesiumkit.Cartesian2(x=12, y=0),
                horizontal_origin=cesiumkit.HorizontalOrigin.LEFT,
            ),
            path=cesiumkit.PathGraphics(
                width=3,
                lead_time=0,
                trail_time=END_SECONDS,
                material=cesiumkit.PolylineGlowMaterial(color=cesiumkit.Color.CYAN, glow_power=0.15),
            ),
        )
    )

    viewer.set_view(cesiumkit.Cartesian3.from_degrees(-76.5, LAUNCH_LATITUDE, 2_500_000))
    return viewer


viewer = build_viewer()

if __name__ == "__main__":
    viewer.show()  # Opens in browser via local HTTP server (Ctrl+C to stop)
