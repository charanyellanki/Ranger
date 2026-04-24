---
title: Device Enrollment Failure
risk_level: medium
applies_to: new_devices, re_enrolled_devices
---

## Symptoms

- New device powered on at a site but never appears in the device registry.
- Device logs repeated "enrollment rejected" errors with various response codes.
- Device is stuck in a bootstrap mode, periodically attempting to reach the enrollment endpoint.
- Fleet dashboard shows a pending-enrollment count that does not decrease.

## Likely Causes

- Device's bootstrap credential is invalid or expired (these are scoped to a specific rollout window).
- The device's pre-shared serial number or MAC address is not in the expected-device whitelist.
- Enrollment endpoint is rejecting due to capacity (rare, but happens during mass deployments).
- Device is on an untrusted network segment — enrollment requires TLS to the authentication server, which may be blocked.
- Time skew between device and enrollment server — the device's initial timestamp may fail the request freshness check.

## Diagnostic Steps

1. Check enrollment endpoint logs for the device's identifier. A rejection with a reason code is fast to resolve; no log at all means the request never arrived.
2. Confirm the device's identifier (serial or MAC) is in the expected-device list for this site or deployment.
3. Verify the bootstrap credential being used is still within its validity window.
4. Confirm the device can reach the enrollment endpoint at the network layer (DNS resolution, TCP connect, TLS establishment).
5. Check the device's clock on its first attempted connection — if it is wildly wrong, the request freshness check will reject even with valid credentials.

## Remediation Steps

1. **Do not auto-remediate enrollment failures.** Enrollment establishes the device identity and is a once-per-lifetime security-critical operation. It must always involve a human with authority to add a device to the fleet.
2. If the failure is a missing whitelist entry, an operator with provisioning permissions adds the device to the whitelist and the device retries on its next cycle.
3. If the bootstrap credential has expired, the deployment batch must be re-issued with a fresh credential before any device will succeed.
4. If network blocks are the cause, coordinate with site networking.

## Escalation Criteria

- Always escalate. The agent's role here is to enrich the ticket with as much diagnostic context as possible so the human resolver has a fast path.
- Critical severity if enrollment rejections spike across a deployment wave — the root cause is almost always configuration, and the wave will fail until it is fixed.

## Risk Level

medium — enrollment is an identity operation. The agent gathers context but never acts.
