# Commissioning Domain V1 — Prepared Production Correction

Status: prepared and disposable-tested; **not executed against production**.

## Current and proposed state

| State | Batch key | Actions | Artifacts | Relationships | Manifest |
|---|---|---:|---:|---:|---|
| Current production | `commissioning-domain-v1-environment-energy` | 8 | 74 | 68 | `5821e12ca1e5666ed6ff39b1a9a2402a9f61e067d56dcd69a1870b5a64333c38` |
| Proposed final composition | `commissioning-domain-v1-environment-energy-final-composition` | 7 | 69 | 60 | `fbee0675ace2b2e256fe1723681e3bd17dd065c670199367d76e8782b352a600` |

The original 71-artifact/95-relationship seed, canonical tables, schema 0016,
publication registry, publication selector, and empty frontend production
registry must remain unchanged.

## Pinned values

- Source commit:
  `08e675e2039d76f16b8c9576e4b5a8254bc44d72`
- Migration SHA-256:
  `b4fffce458ebda4b09ce92cd1998468c4d18bad2450e43e9567776340337a9f7`
- Original artifact/relationship semantic hashes:
  `ab9f580a6a55eafb7848bbb412788202558e78a05cc7b6771714e5a25b0e977d` /
  `feb267bc4cf3e9dbc47b37c816bd59ddbc31e97fe7908244d6005055edc69cf7`
- Final-composition artifact/relationship semantic hashes:
  `57e158f98b0ef0ab15f020cfd31992d73e1222742cfcfaa827574a8eab18974a` /
  `bbc37b284aa43138b53abeffbf6e416fd678806f11fbd95542641cb70c997b21`

## Exact commands

Run from the repository root. The check commands are read-only. The rollback
and apply commands require separate explicit production authorization.

Original batch preflight:

```powershell
python backend/scripts/commissioning_domain_artifact_store.py --check --target production --batch-key commissioning-domain-v1-environment-energy --source-commit 08e675e2039d76f16b8c9576e4b5a8254bc44d72 --manifest-sha256 5821e12ca1e5666ed6ff39b1a9a2402a9f61e067d56dcd69a1870b5a64333c38 --migration-sha256 b4fffce458ebda4b09ce92cd1998468c4d18bad2450e43e9567776340337a9f7
```

Operation A — exact original rollback:

```powershell
python backend/scripts/commissioning_domain_artifact_store.py --rollback --target production --confirm-production-rollback --batch-key commissioning-domain-v1-environment-energy --source-commit 08e675e2039d76f16b8c9576e4b5a8254bc44d72 --manifest-sha256 5821e12ca1e5666ed6ff39b1a9a2402a9f61e067d56dcd69a1870b5a64333c38 --migration-sha256 b4fffce458ebda4b09ce92cd1998468c4d18bad2450e43e9567776340337a9f7
```

Corrected-batch preflight after Operation A:

```powershell
python backend/scripts/commissioning_domain_corrected_artifact_store.py --check --target production --batch-key commissioning-domain-v1-environment-energy-final-composition --source-commit 08e675e2039d76f16b8c9576e4b5a8254bc44d72 --manifest-sha256 fbee0675ace2b2e256fe1723681e3bd17dd065c670199367d76e8782b352a600 --migration-sha256 b4fffce458ebda4b09ce92cd1998468c4d18bad2450e43e9567776340337a9f7
```

Operation B — exact corrected apply:

```powershell
python backend/scripts/commissioning_domain_corrected_artifact_store.py --apply --target production --confirm-production-apply --batch-key commissioning-domain-v1-environment-energy-final-composition --source-commit 08e675e2039d76f16b8c9576e4b5a8254bc44d72 --manifest-sha256 fbee0675ace2b2e256fe1723681e3bd17dd065c670199367d76e8782b352a600 --migration-sha256 b4fffce458ebda4b09ce92cd1998468c4d18bad2450e43e9567776340337a9f7
```

Corrected verification and idempotency use the same pinned values with
`--postcheck` and a second `--apply --confirm-production-apply`.

The earlier
`commissioning-domain-v1-environment-energy-corrected-six-episode` proposal is
preserved as audit history, superseded, and was never applied. Neither
Operation A nor Operation B in this packet has been executed against
production.

## Stop conditions

Stop before mutation if any check shows a mismatched batch key, manifest,
source commit, 74/68 or 69/60 count, semantic hash, migration/schema state,
publication reference, canonical fingerprint, seed count, selector count, or
registry count. Stop if any operation would update an existing artifact,
create a publication row, touch canonical tables, or require migration 0017.

## Recovery

If Operation A succeeds but Operation B fails, leave the database bounded and
unpublished, diagnose the mismatch, and do not improvise. With explicit
recovery authorization, reapply the unchanged original manifest using its
exact apply command and `--confirm-production-apply`, then verify 74/68,
semantic export equality, the 71/95 seed, canonical fingerprints, registry 0,
and selector 0. Do not edit either manifest to force recovery.
