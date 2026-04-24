---
title: MQTT Broker Disconnection
risk_level: low
applies_to: all_mqtt_devices
---

## Symptoms

- Device reports repeated `CONNACK` failures or TCP RSTs on port 8883.
- Broker-side logs show the device connecting, publishing a few messages, then disconnecting.
- Device's last-will message is being observed by the broker periodically.
- Telemetry arrives in bursts rather than the expected steady stream.

## Likely Causes

- Broker capacity saturation — connection cap or message rate throttle tripped.
- Keep-alive mismatch: device's keep-alive interval exceeds the broker's max.
- TLS session resumption failure after a broker restart — device keeps presenting a stale session ID.
- Client ID collision with another device (very bad if you can reproduce it — indicates a fleet provisioning bug).
- Subscription to a topic the device doesn't have ACL permission on, causing the broker to drop the connection after SUBACK failure.

## Diagnostic Steps

1. Check broker-side metrics: current connection count, accepted vs. rejected connects in the last hour, per-client message rates.
2. Compare the device's keep-alive setting against the broker's `keepalive_max`. If the device's is higher, the broker will drop it.
3. Search broker logs for the device's client ID. If two different source IPs are reporting the same client ID, there is a collision.
4. Review the device's published/subscribed topics against the ACL for its credential.
5. If the broker was recently restarted, expect a wave of disconnects as stale sessions are purged — correlate timestamps.

## Remediation Steps

1. **Safe auto-remediation:** issue a `restart` command on the device. This establishes a fresh MQTT session with a new packet ID counter, resolving session-state corruption.
2. If the connection attempts are being rejected at the broker level (not at the device), device-side remediation will not help. Work with the broker operator to check capacity.
3. For ACL mismatches, the device cannot self-heal — the management plane must update the credential's ACL.
4. For client ID collisions, the device's provisioning record must be corrected in the device registry. This requires human review.

## Escalation Criteria

- Restart does not restore the connection within 5 minutes.
- Multiple devices disconnect simultaneously (broker-side fault).
- Client ID collision is confirmed — always escalate, as it may indicate fleet-wide provisioning drift.

## Risk Level

low — device restart is safe. Broker-side faults cannot be auto-remediated from the device, so escalate cleanly.
