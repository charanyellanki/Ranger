---
title: Battery Drain Faster Than Expected
risk_level: medium
applies_to: battery_powered_devices
---

## Symptoms

- Battery percentage is declining significantly faster than the device's published duty-cycle would predict.
- Expected remaining runtime shortened from weeks to days without a corresponding configuration change.
- Device wake-cycle telemetry (if exposed) shows more wake events per hour than the configured reporting interval would require.
- Radio transmission count is elevated beyond the expected transmission count for the device's reporting schedule.

## Likely Causes

- Device is caught in a retry loop (repeated connection attempts that each consume full TX power).
- A sensor peripheral has failed in a way that holds the main MCU awake (bus stuck, interrupt storm).
- Firmware regression that disabled or shortened the deep-sleep window.
- Environmental: persistent cold temperatures reducing effective battery capacity.
- Configuration was changed to a more aggressive reporting interval without a corresponding battery-budget review.

## Diagnostic Steps

1. Compare the device's current reporting interval and wake-cycle count against the configuration baseline.
2. Pull the device's last 48 hours of signal strength and transmission success rate. Poor connectivity drives retry loops that are invisible at the app layer but expensive at the radio layer.
3. Check whether the device has recent firmware updates; compare battery life before and after.
4. Correlate the drain rate with ambient temperature telemetry. Lithium chemistry can lose 20–40% capacity at cold temperatures.
5. Compare with peer devices (same model, same firmware, same site) to isolate whether the issue is device-specific or fleet-wide.

## Remediation Steps

1. **Safe auto-remediation:** issue a `sync` command. Re-applying the canonical config resolves a surprising amount of drain — many cases are drift from an earlier push.
2. If sync does not help and signal strength suggests the device is in a retry loop, a `restart` clears the radio state machine.
3. If the drain rate does not improve within 2 hours after remediation, schedule a battery replacement pre-emptively and a physical inspection — a peripheral fault is likely.
4. Do **not** modify the reporting interval or disable features to "extend" battery life without operator approval. That silently degrades the data the device was deployed to collect.

## Escalation Criteria

- Drain rate does not normalize after sync + restart.
- Multiple devices of the same model or site show correlated drain onset — probable firmware regression, escalate to platform.
- Device is safety-critical and projected runtime is under 48 hours.

## Risk Level

medium — safe auto-remediations exist, but persistent drain indicates hardware or firmware root cause that requires human investigation.
