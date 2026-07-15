# ZIP Overlap Sensitivity and Bounded Mapping-Stage Design V1

> Read-only analysis. Area overlap is not population share, address dominance, or a definitive representative lookup.

## Source and safety

- Official source SHA-256: `57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77` (verified: `True`)
- Accepted / rejected rows: `39967` / `430`
- Production ZIP mapping rows before / after: `0` / `0`
- Production auto-select eligible: `0`

## Sensitivity results

| Policy | Rows | No mapping | One district | Same-state multi | Multi-state | Ambiguous |
|---|---:|---:|---:|---:|---:|---:|
| `policy_a_any_accepted` | 39967 | 0 | 27780 | 5725 | 137 | 5862 |
| `policy_b_positive_total` | 39967 | 0 | 27780 | 5725 | 137 | 5862 |
| `policy_c_positive_land` | 39930 | 0 | 27813 | 5692 | 137 | 5829 |
| `policy_d_gt_0_percent` | 39930 | 0 | 27813 | 5692 | 137 | 5829 |
| `policy_d_gte_0_01_percent` | 39898 | 0 | 27838 | 5667 | 137 | 5804 |
| `policy_d_gte_0_05_percent` | 39800 | 0 | 27919 | 5586 | 137 | 5723 |
| `policy_d_gte_0_1_percent` | 39719 | 0 | 27984 | 5522 | 136 | 5658 |
| `policy_d_gte_0_5_percent` | 39343 | 0 | 28296 | 5219 | 127 | 5346 |
| `policy_d_gte_1_percent` | 39077 | 0 | 28521 | 5004 | 117 | 5121 |
| `policy_d_gte_2_percent` | 38686 | 0 | 28854 | 4683 | 105 | 4788 |
| `policy_d_gte_5_percent` | 37953 | 0 | 29509 | 4043 | 90 | 4133 |
| `policy_d_gte_10_percent` | 37140 | 0 | 30246 | 3325 | 71 | 3396 |
| `policy_d_gte_25_percent` | 35572 | 0 | 31717 | 1894 | 31 | 1925 |
| `policy_d_gte_50_percent` | 33600 | 42 | 33600 | 0 | 0 | 0 |

## Measured overlap findings

- Water-only relationships: `37` across `37` ZCTAs.
- Zero-area relationships: `0`.
- Integrity anomaly full-list checksum: `5588ed9c1d8c67b3ee169f0aa193d543e6f33ce780edbb60a5e54572c90c5223`.

## Decision boundary

- Possible mappings: area evidence supports preserving all official relationships with raw land/water provenance.
- Ranked mappings: land share can support an explicitly labeled, versioned presentation order, but cannot claim where residents or addresses are concentrated.
- Auto-select: unsupported and disabled. Reducing ambiguity with a threshold does not establish correctness.
- ZCTAs are Census approximations, not USPS ZIP delivery boundaries. Land share is not population share, and area dominance does not prove address dominance.
- Recommended next accuracy source: both Census block-level population allocation and a full-address congressional-district lookup; population weighting improves ZIP-level ranking evidence, while address lookup is needed for automatic representative selection.

## Staging decision

The existing `zip_district_mappings` table cannot reproduce raw area evidence or policy decisions. The candidate additive migration separates immutable snapshots/artifacts/relationship evidence from versioned policy evaluations. It remains unapplied.

## Product-use decision table

| Use | Any overlap | Positive land | Min land share | Dominance/margin | Block population | Full address |
|---|---|---|---|---|---|---|
| Display all possible districts | yes | incomplete alone | incomplete alone | no | yes | yes |
| Order possible districts | weak | weak | policy-sensitive | useful presentation aid | stronger ZIP-level evidence | definitive for address |
| Hide water-only by default, retain evidence | supports | supports | not needed | not needed | supports | supports |
| Label low material overlap | raw area only | raw area only | supports versioned label | supports versioned label | stronger context | supports |
| Ask for street address | supports need | supports need | supports need | supports need | still useful | fulfills request |
| Automatically choose representative | no | no | no | no | no | yes |

No production or runtime mutation occurred.
