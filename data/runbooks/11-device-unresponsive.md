---
title: Device Unresponsive / Hung State
risk_level: medium
applies_to: all_devices
---

## Symptoms

- Device is online at the network layer (responds to management-plane pings) but has stopped publishing telemetry.
- TCP connection to the broker appears healthy in netstat, but no MQTT PUBLISH packets in over 10 minutes.
- Device's watchdog telemetry (if exposed) shows the main application thread blocked.
- Memory or CPU telemetry (last known) was trending upward before the hang.

## Likely Causes

- Application-level deadlock — two threads waiting on each other.
- Memory leak exhausted heap, causing the OS to swap-thrash or kill the application.
- Stuck I2C/SPI transaction blocking the main loop while the network stack continues running on a separate core.
- Firmware bug with a specific sensor configuration — check if this firmware + sensor combination has a known advisory.
- Stack overflow in a rarely-executed code path.

## Diagnostic Steps

1. Confirm the device responds to a `status` call. If it returns any data, the network stack is alive and this is an application hang, not a connectivity issue.
2. Pull the last 30 minutes of telemetry. Compare memory and CPU trends — a slow upward curve that caps out is classic resource exhaustion.
3. Check whether other devices of the same model + firmware version are exhibiting the same pattern.
4. If crash dumps are enabled, the device may have already written one — check the management-plane dump bucket.
5. Review recent configuration changes pushed to this device. A new sensor polling interval is a common trigger.

## Remediation Steps

1. **Safe auto-remediation:** issue a `restart` command. For a hung-application-but-healthy-network device, restart almost always recovers it. Success rate ~90%.
2. Give the device 2 minutes to come back, then verify it resumes publishing telemetry at its normal rate.
3. If the device hangs again within 1 hour of restart, classify as recurrent hang and escalate. Avoid endless restart loops — they mask the underlying bug.
4. After successful recovery, open a low-priority ticket to capture the conditions for post-hoc analysis. One-off hangs happen; patterns matter.

## Escalation Criteria

- Restart fails to restore telemetry.
- Device hangs again within 1 hour after a successful restart.
- Multiple devices of the same model + firmware version hang within the same 24-hour window (fleet-wide firmware issue).
- Device holds safety-critical data that was not persisted before the hang.

## Risk Level

medium — restart is safe once, but the router should prevent runaway remediation. Cap at 2 restart attempts per device per hour, then escalate.
