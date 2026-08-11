# Rocket stage separation

_Example — Transfer position and velocity from a booster to a second stage at deployment, then propagate both stages independently._

This example uses a deliberately simple local kinematic model to make the
state handoff easy to see. It is a visualization example, not a realistic
flight-dynamics simulation.

The important part is the deployment event:

```python
separation_state = joined_ascent[-1]
second_stage_initial_state = replace(separation_state)
```

That copies both position and velocity. Afterward, each stage is propagated
with its own acceleration. The second stage's first Cesium position sample is
at separation, so it does not appear before deployment.

Run the complete example:

```bash
python examples/12_rocket_stage_separation.py
# Opens in browser — Ctrl+C to stop the server
```

[View the complete Python source](https://github.com/link2427/cesiumkit/blob/main/examples/12_rocket_stage_separation.py).
