---
title: Storage Facility Gateway Offline
risk_level: high
applies_to: storage_facility_gateways, warehouse_gateways
---

## Symptoms

- Gateway device has not reported in for longer than the expected heartbeat interval.
- All downstream sensors that route through this gateway are also silent.
- Site network monitoring shows the gateway's uplink is still active (if it has one separate from the sensor mesh).
- Operational dashboards for the facility show no new sensor readings across multiple zones.

## Likely Causes

- Gateway power event — loss of mains with backup battery that has not yet failed over, or a failed UPS.
- Gateway itself is in a hung state (see the unresponsive runbook).
- Uplink failure (cellular or WAN) isolating the gateway from the control plane while it continues to collect locally.
- Firmware update in progress — cross-check the rollout plan.
- Physical damage (the gateway enclosure is in a warehouse; forklift strikes happen).

## Diagnostic Steps

1. Confirm the gateway's specific diagnostic interface is reachable. Most enterprise gateways have a secondary out-of-band channel.
2. Check facility power telemetry. Mains failure often correlates with simultaneous silence from every powered-wired device in the facility.
3. Verify the local sensor mesh is still intact by checking downstream sensor telemetry in the gateway's local buffer (if the uplink restores, backfilled data will arrive).
4. Review the last 15 minutes of telemetry for rising temperatures, connectivity errors on the uplink interface, or firmware update events.
5. Check work order system for any scheduled maintenance.

## Remediation Steps

**Because the gateway is infrastructure, not a single sensor, the blast radius of any action is high. Treat remediation conservatively:**

1. If the gateway is still reachable on the management interface, attempt a `sync` first — not a restart. Sync restores the uplink without losing local buffer state.
2. Only issue a `restart` if sync fails AND the gateway has been silent for more than 15 minutes AND site personnel confirm no active maintenance. A restart drops in-flight local sensor data.
3. If the gateway is fully unreachable, the incident requires on-site presence. Do not attempt further remote action.

## Escalation Criteria

- Always escalate gateway-level incidents to the facility operations team regardless of the remediation outcome. Facility operators own the gateway and need to know.
- Critical severity if the facility is regulated (cold-chain, pharmaceuticals, secure asset storage) and sensor silence exceeds 10 minutes.
- Critical severity if this gateway's silence correlates with adjacent facilities' gateways going silent (upstream network event).

## Risk Level

high — gateway remediation affects downstream sensor fleet. Route only low-risk sync through the agent; restart requires human confirmation.
