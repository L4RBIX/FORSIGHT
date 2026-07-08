# Physical Grounding Notes

Foresight should be presented as grounded only when the demo setup has real measurements.

## Measure before presenting

Record 30 seconds of a static AprilTag and compute:

- Position standard deviation in millimeters.
- Rotation standard deviation in degrees.
- Frame drop rate.
- Detection confidence range.

The placeholder values are:

```text
position jitter: +/-4.0 mm
rotation jitter: +/-1.8 deg
```

Replace them with real values before final judging.

## Simulation uncertainty

Monte Carlo runs should vary:

- Object position.
- Object orientation.
- Mass.
- Friction.
- Push force.

The safety decision should quote failure count and total simulations.
