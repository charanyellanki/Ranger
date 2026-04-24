---
title: TLS Certificate Expiry Renewal
risk_level: medium
applies_to: all_devices_with_device_identity_certs
---

## Symptoms

- Device reports TLS handshake failure against the management plane or broker.
- Certificate renewal job failed silently for this device in the last expected rotation window.
- Device's cert `notAfter` is within 14 days of the current time, or already in the past.
- Fleet dashboard shows an increase in handshake failures correlated with a batch of devices sharing the same issuance date.

## Likely Causes

- Certificate rotation system did not reach the device before expiry (device was offline during the window).
- Device's root CA trust store is missing the new issuing CA (if the CA itself was rotated).
- Private key on the device is corrupted — the device can no longer produce a valid CSR.
- The renewal endpoint's credential has itself expired — meta issue where the system that issues certs can't authenticate to anyone.
- Clock drift is causing the device to perceive a valid cert as expired (see clock drift runbook).

## Diagnostic Steps

1. Check the device's current certificate `notAfter` field. Compare to the current server time.
2. Confirm the device's clock is within NTP tolerance before concluding the cert is actually expired.
3. Verify the rotation pipeline ran successfully for this device's cohort. Check the pipeline's logs for errors.
4. Pull the device's trust store and confirm the expected issuing CA is present.
5. If many devices failed, check for a common issuance date — all devices from one cohort will hit expiry within the same window.

## Remediation Steps

1. **Do not auto-remediate certificate operations.** Certificate issuance is a trusted-CA action with auditable consequences — always route through the renewal pipeline.
2. If the renewal pipeline is healthy but missed this device, manually trigger a renewal job for this specific device through the management plane.
3. If the root cause is clock drift, resolve the drift first, then confirm the existing cert is actually valid.
4. If the private key is corrupted, the device must be re-enrolled — a destructive action that regenerates the device identity. Requires approval from the fleet operator.

## Escalation Criteria

- Always escalate. Even the "safe" action (triggering a renewal job) is a signed operation that should have a human on the approval trail for audit.
- If more than 10 devices in a cohort are affected, declare an incident and page the platform-on-call.
- If the issuing CA itself has expired or been compromised, engage security leadership immediately — this is a fleet-wide outage.

## Risk Level

medium — renewal via the pipeline is safe, but identity operations must be audited. Agent always escalates.
