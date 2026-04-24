---
title: Unusual Access Pattern Investigation
risk_level: medium
applies_to: all_devices_with_management_interfaces
---

## Symptoms

- Telemetry query rate from a specific operator or credential is 10× or more the 30-day baseline.
- Management commands are issued outside normal business hours from a credential that has never done so before.
- A credential that is normally used against a single site suddenly queries devices across multiple sites within a short window.
- Bulk export operations that have no corresponding audit ticket.

## Likely Causes

- Legitimate but urgent operational work (troubleshooting, bulk maintenance) where the operator did not file an expected audit ticket.
- Authorized automation ran an unusual query pattern — check for scheduled jobs or tooling changes.
- A credential was shared between operators (policy violation but not malicious).
- Credential compromise — pair with the unauthorized access runbook if source IP is also anomalous.
- Legal or compliance-driven bulk extraction that bypassed normal channels (rare but real).

## Diagnostic Steps

1. Compare the observed pattern against the credential's 30-day baseline. `deviation_score` above 3σ warrants investigation.
2. Cross-reference with the operator's change tickets and on-call schedule. Legitimate urgent work usually has a paper trail.
3. Check the source IP addresses. A credential consistently used from one office suddenly arriving from a data center IP is a strong anomaly.
4. Look at the specific commands used. Read-only queries are lower risk than config writes.
5. Contact the operator directly through a known-good channel (not the suspected compromised one) to confirm or deny.

## Remediation Steps

**Do not auto-remediate.** This is an investigation path, not a remediation path:

1. Do not rotate or disable the credential yet — preserve forensic linkage until the investigation determines whether the activity is authorized.
2. Enable enhanced logging on the credential for the next 24 hours. Capture full request bodies, not just headers.
3. If the investigation determines the activity was unauthorized, proceed to the unauthorized access runbook.
4. If it was authorized but violated policy (shared credential, missing ticket), open a policy violation ticket, not a security incident.

## Escalation Criteria

- Any unusual access pattern with writes (not just reads) escalates immediately.
- Access pattern spans multiple sites or asset classes that the credential should not have needed — escalate immediately.
- Inability to contact the credential's owner through a known-good channel within 30 minutes — treat as potential compromise.

## Risk Level

medium — ambiguous signal. Escalate for human judgement rather than guessing.
