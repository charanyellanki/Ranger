---
title: Firmware Update Failure Recovery
risk_level: high
applies_to: all_ota_capable_devices
---

## Symptoms

- Device reports `firmware_update_failed` event or `update_rolled_back`.
- Device stuck in bootloader mode — replying to pings but not presenting full telemetry schema.
- Version string reports "recovery" or mismatches the target version after a deployment wave.
- Repeated restart loops with crash dumps uploaded at boot.

## Likely Causes

- Power loss during flash write (common on battery devices with marginal charge).
- Corrupted firmware image — verify the image signature matches the one on the update server.
- Insufficient free storage on the device for the new image plus rollback copy.
- Target version is incompatible with the device's bootloader version.
- Network interruption mid-download causing truncated image.

## Diagnostic Steps

1. Fetch the device's last 10 boot records. A pattern of boot → crash → boot indicates corrupted active image.
2. Verify the firmware image on the update server has a valid signature matching the device's trust store.
3. Check device's reported free storage before the update attempt. Needs at least 2× the image size for dual-slot devices.
4. Compare target version's minimum bootloader requirement against device's actual bootloader version.
5. Pull the device's upload of its last crash dump, if available.

## Remediation Steps

**Do not auto-remediate firmware failures.** This runbook's remediation steps are all destructive or require human judgement:

1. If the device is in stable recovery mode, trigger a rollback to the last known-good version via the management plane. This requires an operator to confirm which version to roll back to.
2. If the device is in a boot loop, no OTA recovery is possible — physical access is needed to reflash via debug port.
3. If the failure affected a fleet wave, **pause the rollout immediately**. Do not attempt individual device recovery until the root cause of the wave failure is understood.
4. After successful recovery, file a post-mortem ticket with the crash dump and firmware image hashes.

## Escalation Criteria

- Any firmware update failure — always escalate. Firmware state changes are destructive and must involve a human.
- More than 2% of a rollout wave fails — pause the wave and open an incident.
- Device is in a boot loop and reports crash telemetry that references a kernel module outside the update's changeset (possible pre-existing fault exposed by the update).

## Risk Level

high — firmware operations can brick devices. The agent must always escalate, never auto-remediate.
