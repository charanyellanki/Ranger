---
title: Tamper Alert Investigation
risk_level: high
applies_to: security_sensors, asset_trackers, enclosure_monitored_devices
---

## Symptoms

- Device reports `tamper_event` with flags such as `enclosure_opened`, `accelerometer_shock`, or `magnetic_seal_broken`.
- Unexpected motion on a static device (accelerometer above threshold while device should be stationary).
- Enclosure switch transitioned from `closed` to `open` outside of a scheduled maintenance window.
- GPS location drift beyond the configured geofence for asset trackers.

## Likely Causes

- Legitimate but unscheduled maintenance (technician forgot to open a maintenance window).
- Device physically moved during facility reorganization without updating asset records.
- Sensor fault — accelerometer false-positives are common on devices mounted near HVAC compressors.
- Actual unauthorized physical access — treat as the default hypothesis until the other causes are ruled out.

## Diagnostic Steps

1. **Do not assume a false positive.** Check the scheduled maintenance calendar for an approved window covering this device and time.
2. Pull the device's last 30 minutes of sensor telemetry — look for vibration, temperature, or light-sensor changes consistent with enclosure opening.
3. Check facility access logs for badge entries near the device's location within ±10 minutes.
4. Review camera footage if available and permitted by site policy.
5. Check whether adjacent devices reported any related events (cascading tampers suggest malicious sweep).

## Remediation Steps

**This runbook never auto-remediates.** Physical security events require human judgement:

1. Open a high-priority security ticket and page the on-duty security officer.
2. Preserve all telemetry for the affected device for the past 24 hours (extend from default retention).
3. If the device type supports it, mark the device as quarantined in the device registry — new data continues to be collected but no management commands are honored until the incident is cleared.
4. Do not issue a sync, restart, or reset_auth while the investigation is open — any of these can destroy forensic state.

## Escalation Criteria

- Every tamper event escalates by default.
- If the device is in a regulated asset class (controlled substances, financial records, critical infrastructure), also notify compliance.
- If multiple devices within the same zone report tampers within 15 minutes, treat as a potential site-wide breach and invoke the incident response plan.

## Risk Level

high — physical security signal. Auto-remediation is never appropriate; the agent must escalate every time.
