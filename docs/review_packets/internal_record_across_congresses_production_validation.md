# Internal Record Across Congresses Production Validation

Validation date: 2026-06-25

Backend URL: `https://political-fingerprint.onrender.com`

## Result

Production validation passed for the guarded internal `Record Across Congresses` route.

## Checks

| Check | Result |
| --- | --- |
| Token availability | `INTERNAL_API_TOKEN` loaded from ignored local environment file; present and non-empty; value not printed, logged, or committed |
| `/health` | `ok` |
| `/coverage/metadata` | database-backed: `data_source = database` |
| Public OpenAPI forbidden route scan | Passed; zero public paths contained `internal`, `record-across`, `record`, `congress`, `comparable`, or `family` |
| Unauthenticated internal route request | `401` |
| Wrong-token internal route request | `401` |
| Authorized Valerie Foushee request | `200` |
| Authorized Aaron Bean spot check | `200` |
| Authorized Abraham J. Hamadeh spot check | `200` |
| Authorized James Gallagher spot check | `200` |

## Response Shape Findings

Authorized Valerie Foushee response included:

- `product_framing = Record Across Congresses`
- `response_kind = internal_house_record_across_congresses_family_evidence`
- explicit `non_authorization_metadata`
- separated `cast_substantive_yes_count`, `cast_substantive_no_count`, `not_voting_count`, `present_count`, and `missing_no_record_count`

No disallowed continuity/change claim fields were found:

- `continuity`
- `change`
- `movement`
- `trend`
- `consistency`
- `changed-position`

## Exposure And Product Boundary

No public OpenAPI exposure was found for the internal route or related internal route vocabulary.

No continuity, change, movement, trend, consistency, or changed-position claims were exposed in the authorized response.

No production writes were performed.
