---
title: Wi-Fi Connectivity Loss Diagnosis
risk_level: low
applies_to: wifi_connected_devices
---

## Symptoms

- Device last-seen timestamp exceeds the expected heartbeat interval (typically 5 minutes).
- No corresponding alert from the site's network monitoring (rules out full site outage).
- Signal strength (RSSI) trending below -80 dBm in the hours prior to disconnection.
- Neighboring devices on the same SSID remain connected — isolates fault to this device or its local RF environment.

## Likely Causes

- DHCP lease expiry combined with AP failing to renew.
- Wi-Fi driver hang on the device after extended uptime (common past 30 days continuous).
- AP channel congestion triggering repeated association failures.
- TLS handshake failure with the MQTT broker after a certificate rotation on the backend.
- Physical displacement or new obstruction between device and AP.

## Diagnostic Steps

1. Confirm the AP serving this device is online and reporting clients. Check the network management console for client count on that AP.
2. Pull the device's last 30 minutes of telemetry before disconnect. Look for RSSI decline, auth failures, or IP address changes.
3. Check whether the device's last successful TLS handshake matches the current broker certificate fingerprint.
4. Query neighboring devices for the same alert pattern — multiple simultaneous disconnects imply AP or broker fault, not device fault.
5. Verify the device's firmware version has no known Wi-Fi driver advisories.

## Remediation Steps

1. **Safe auto-remediation:** issue a `sync` command. The device retries DHCP and re-associates with the strongest available AP. Resolves ~60% of cases.
2. If sync fails, issue a `restart` command. The device performs a full reboot, which clears stale driver state. Resolves ~25% of remaining cases.
3. If the device does not come back online within 5 minutes of restart, escalate to on-site technician for physical inspection.
4. After recovery, monitor for 15 minutes. If disconnections recur within the hour, treat as persistent and escalate.

## Escalation Criteria

- Device fails to come back online after `sync` + `restart` attempts.
- More than 5 devices on the same AP disconnect within a 15-minute window (AP fault, not device fault).
- Disconnection coincides with a broker certificate event logged within the last 6 hours.

## Risk Level

low — sync and restart are idempotent and non-destructive. Safe for auto-remediation.
