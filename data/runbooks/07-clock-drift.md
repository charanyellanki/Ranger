---
title: Clock Drift Correction
risk_level: low
applies_to: all_devices_with_rtc
---

## Symptoms

- Device's reported timestamp deviates from NTP reference by more than 30 seconds.
- TLS handshakes fail with "certificate not yet valid" or "certificate expired" errors even though the broker certificate is current.
- Event ordering in telemetry appears shuffled relative to neighboring devices.
- Scheduled jobs on the device fire at the wrong wall-clock time.

## Likely Causes

- Battery-backed RTC battery (coin cell, separate from main battery) has failed.
- Device has not been able to reach NTP servers (firewall change, upstream outage).
- Firmware bug — certain vendor SDKs drift by ~1 second per day even when NTP is configured.
- Device was offline for an extended period and its RTC drifted.
- Intentional tampering (rare — pair with the tamper runbook if tamper flags also tripped).

## Diagnostic Steps

1. Compare the device's last reported timestamp against the server's receive timestamp. Persistent offset in one direction indicates systematic drift, not intermittent network delay.
2. Confirm the device has NTP servers configured and that they are reachable from the device's network segment.
3. Check whether other devices on the same network segment show similar drift. Widespread drift points to NTP or firewall issue upstream.
4. Verify the device's RTC battery status, if that telemetry field is exposed.

## Remediation Steps

1. **Safe auto-remediation:** issue a `sync` command. For most device families, sync includes a forced NTP re-synchronization. Resolves ~80% of clock drift cases.
2. If sync does not resolve the drift (verify in the next heartbeat), issue a `restart` — some firmwares only re-run NTP at boot.
3. If drift persists after both, the RTC battery has likely failed. Schedule physical replacement.
4. If TLS failures are the symptom, after correcting the clock, expect a temporary spike in handshake traffic as the device re-establishes every cached connection.

## Escalation Criteria

- Drift returns within 24 hours of successful correction (suggests RTC battery failure, needs physical service).
- Multiple devices on the same network show simultaneous drift onset (upstream NTP or firewall issue, not a device problem).
- Device is in a regulated context where timestamp accuracy is auditable (medical, financial) and drift exceeded regulatory tolerance.

## Risk Level

low — sync and restart are idempotent and safe for auto-remediation.
