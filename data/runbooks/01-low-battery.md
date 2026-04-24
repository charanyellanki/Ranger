---
title: Low Battery Replacement Procedure
risk_level: low
applies_to: battery_powered_sensors, wireless_gateways
---

## Symptoms

- Device reports battery level below 20% in telemetry `battery_percent` field.
- Battery voltage telemetry (`bat_mv`) trends downward over 48–72 hours with no recovery.
- Intermittent disconnections, typically clustered in cold ambient conditions.
- Transmission intervals extend as firmware enters power-saving mode.

## Likely Causes

- Normal depletion at end of duty cycle (primary lithium cells).
- Cold-temperature capacity loss in lithium-ion packs (below 0°C).
- Firmware bug causing excessive radio wake-ups (check firmware changelog).
- Stuck-awake condition from a failing environmental sensor holding the main MCU out of sleep.

## Diagnostic Steps

1. Fetch the most recent 24 hours of `battery_percent` and `bat_mv` readings from telemetry.
2. If the slope is linear and matches expected depletion for the device class, classify as routine replacement.
3. If the slope is steeper than expected (more than 2× baseline), check the device's wake cycle count — an elevated count points to firmware or sensor fault.
4. Verify ambient temperature at device location. Lithium-ion capacity drops ~20% at -10°C.
5. Confirm physical access is possible within the maintenance window.

## Remediation Steps

1. Schedule a battery swap through the facilities ticketing system. Do **not** dispatch an emergency technician unless the device is safety-critical.
2. If firmware bug is suspected, queue a firmware update after battery replacement — never before, as a mid-update power loss bricks the device.
3. Update the device's expected-replacement date in the asset inventory.
4. After replacement, verify the device rejoins the mesh and reports battery > 95% within 10 minutes.

## Escalation Criteria

- Battery drains faster than expected on more than 3 devices in the same site within 30 days (indicates a fleet-wide firmware or environmental issue).
- Device is safety-critical (cold-chain monitoring, security alarm) and has less than 12 hours of projected runtime.
- Battery compartment shows physical damage, swelling, or electrolyte leakage — follow hazardous materials handling procedure.

## Risk Level

low — routine maintenance; no remote remediation is both feasible and safe (the agent cannot swap a battery).
