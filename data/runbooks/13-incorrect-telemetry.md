---
title: Device Reports Incorrect Telemetry Values
risk_level: medium
applies_to: sensor_devices
---

## Symptoms

- Sensor reports values that are physically implausible (negative humidity, temperatures outside manufacturer range).
- Values are constant regardless of actual environmental change (stuck sensor).
- Values are consistent with the sensor's stuck-at-zero or stuck-at-full-scale failure modes.
- Values differ significantly from a nearby redundant sensor measuring the same quantity.
- Calibration drift — values appear correct but have a consistent offset from a trusted reference.

## Likely Causes

- Sensor hardware failure (end of service life, component fatigue).
- Sensor disconnected or loose in the enclosure (loose cable, corroded contact).
- Environmental contamination (dust on optical sensor, condensation on capacitive sensor).
- Firmware reading the wrong register after a driver update.
- Configuration drift — sensor scale factor or offset was changed unintentionally.

## Diagnostic Steps

1. Compare the suspect device's readings against a known-good redundant sensor at the same location, if available.
2. Check the sensor's self-diagnostic register. Most industrial sensors have a health bit that flips before catastrophic failure.
3. Review the last 7 days of readings for discontinuities. A sudden step change often correlates with a firmware update or configuration push.
4. Verify the firmware's reported sensor driver version matches the expected one for this device model.
5. Request the site operator to do a physical inspection if the cause is not evident from telemetry alone.

## Remediation Steps

1. **Safe auto-remediation:** issue a `sync` command to re-apply the device's canonical configuration. Resolves configuration drift.
2. If configuration is not the cause, issue a `restart` to clear any transient sensor driver state.
3. If the sensor continues to report incorrect values after both, the cause is almost certainly hardware. Remote remediation cannot fix this — the device needs physical service.
4. Do **not** attempt to "recalibrate" remotely by adjusting offsets in software. This masks hardware failure and creates a long-term integrity problem for downstream analytics.

## Escalation Criteria

- Incorrect readings persist after sync + restart. Dispatch technician for physical inspection.
- Readings are being used for regulatory reporting (cold chain, environmental compliance). Immediately mark the data as suspect to prevent downstream integrity issues.
- Multiple sensors of the same model show correlated drift — fleet-wide issue, likely firmware.

## Risk Level

medium — sync and restart are safe, but if those fail, hardware issues require human action. Do not loop remediation attempts.
