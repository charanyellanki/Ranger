---
title: Cellular Connectivity Loss Diagnosis
risk_level: medium
applies_to: lte_devices, nb_iot_devices, cellular_gateways
---

## Symptoms

- Device absent from heartbeat stream for longer than the expected reporting interval.
- Last-known `rsrp` value below -115 dBm or `rsrq` below -15 dB.
- PDP context activation failures logged in the last 24 hours.
- Billing/usage dashboard shows zero data in the current billing cycle for this SIM.

## Likely Causes

- SIM suspended for non-payment or reached data cap.
- Carrier network outage in the device's coverage area.
- Antenna disconnected, damaged, or misaligned.
- Firmware modem driver hang — increasingly common on devices with uptime over 60 days.
- APN configuration drift after a modem firmware update.
- Device physically moved into a cellular dead zone (e.g. interior of a new steel-frame structure).

## Diagnostic Steps

1. Check the SIM management portal for the device's MSISDN/ICCID. Confirm SIM is active and within data allowance.
2. Cross-reference with carrier status pages for outages affecting the device's region.
3. Query neighboring cellular devices at the same site — widespread disconnection points to carrier fault.
4. Pull the device's last successful connection record. If the RSRP was already marginal, physical relocation may be the root cause.
5. Verify firmware version does not have open modem advisories.

## Remediation Steps

1. **Safe auto-remediation:** issue a `restart` command if the device is still reachable over its management channel. Cycles the modem, reattempts network registration.
2. If the device is fully unreachable, no remote action is possible. Dispatch is required.
3. For suspected APN drift: push a configuration sync via the management plane (device-class-specific — see APN runbook).
4. If the SIM is suspended, work with carrier account owner to restore service before any device-side action.

## Escalation Criteria

- Device remains offline more than 30 minutes after restart attempt.
- More than 3 devices on the same carrier in the same cell tower range go offline simultaneously.
- Carrier billing system shows unexpected data spike immediately before disconnection (possible compromise — follow unauthorized access runbook).

## Risk Level

medium — cellular restarts have a small probability of leaving the device stuck in airplane mode if the modem firmware is buggy. Prefer automated retry with a hard cap of 2 attempts.
