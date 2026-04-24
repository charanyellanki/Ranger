---
title: Unauthorized Access Attempt Response
risk_level: high
applies_to: all_devices_with_management_interfaces
---

## Symptoms

- Device logs repeated authentication failures from the management plane.
- Successful authentication from an IP address outside the expected management range.
- API calls using a credential that was rotated or revoked.
- Device's audit log shows management commands issued by an identity that does not match the expected operator pool.

## Likely Causes

- Credential leak — an operator's API key or certificate was exposed (git commit, screenshot, phishing).
- Compromised bastion host — attacker pivoted from a trusted network segment.
- Insider misuse of legitimate credentials.
- Automated scanning or brute force from the open internet (common if the management plane has any public exposure).
- Legitimate access from a non-standard location that failed to go through the normal VPN (user error, not malicious).

## Diagnostic Steps

1. Confirm the source IP is not part of any known legitimate range (VPN pool, cloud NAT egress, office networks).
2. Determine which credential was used and who it was issued to. Check the credential's issuance and last-rotation timestamps.
3. Review what management actions were attempted or succeeded. The action set indicates intent — read-only probing vs. config writes vs. data exfiltration.
4. Check whether the same credential was used successfully against other devices in the fleet. A compromised credential is rarely used against a single target.
5. If the device action log shows any data exfiltration (e.g. bulk telemetry pulls), mark the incident severity as critical.

## Remediation Steps

**This is always a critical-severity path. The agent escalates immediately without attempting any device-side action.**

1. Do **not** issue `reset_auth` yet — rotating the credential destroys forensic linkage between the attacker and the compromised credential. Wait for security team guidance.
2. If the attacker appears to have active management access (successful writes in the last 10 minutes), the security team may request immediate network isolation — a separate network-level action, not a device command.
3. Preserve the device's full audit log. Extend retention on the management plane for any API calls using the suspicious credential across the fleet.

## Escalation Criteria

- Every event in this category escalates. Always.
- Critical severity if any of: successful write action, data exfiltration, credential used against ≥3 devices.

## Risk Level

high — security-critical. Never auto-remediate; always escalate and preserve state.
