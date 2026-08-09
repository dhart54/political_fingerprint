# M11B National Security Full-Record Interpretation Source Readiness V1

## Review decision requested

Mechanically review the non-authorizing source-readiness packet for the exact
M11A-approved F000477 National Security & Foreign Policy 119th-Congress
universe. Do not review or infer action meanings, episodes, propositions,
Semantic IR, synthesis, or public wording from this packet.

## Immutable input boundary

- M11A merge and M11B branch base: `434c972132e99628bddec4cc6392adc741e03205`
- Universe authority receipt:
  `universe-authority:f000477:national_security_foreign:119:v1`
- Receipt digest:
  `89b7a27236ab0256b867c2525627408d84c6493c982c474ec4de3c2c36e79c87`
- Approved actions: `82`
- Approved action-set digest:
  `190bda45c25cd32ae0a6847c862f85837eafc4a82dfda237746a66467c550400`
- Universe-subject digest:
  `b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5`
- Selection digest:
  `a018b597705132f0e891c575af1dac4b880c31b0d98469f2f47001982dce0b81`
- Official cutoff: July 23, 2026 through `house:119:2:283`

No M11A proposal, selection, source-inventory, authority-receipt, or action-set
membership changed.

## Source acquisition and readiness result

The bounded acquisition covered only the approved universe:

- 50 Congress.gov whole-measure action lists;
- 50 Congress.gov text-version indexes;
- 49 selected official Congress.gov XML operative texts;
- 32 exact amendments resolved through five already-acquired official
  Congress.gov amendment-index records;
- 82 already-acquired official House Clerk roll-call records; and
- the already-governed July 20, 2026 House Rules Committee report for H.R. 8800
  final passage.

The governed packet contains 186 unique content-addressed raw files totaling
23,375,949 bytes. Raw official provenance is separate from the closed neutral
source projections.

Readiness result:

- `82` `ready_for_action_interpretation`
- `0` blocked
- artifact identity:
  `interpretation-source-readiness:f000477:national_security_foreign:119:v1`
- artifact file digest:
  `30f6f64b693d3adbe3833a5ab09ab04c9ba4728dd7d1eb818ab65f69ba9258fc`
- source-readiness subject digest:
  `58e6f4d017a4f8cd59a38a3d78e80878985fc850560974ca981e5f4b22762499`

## Stage edge cases mechanically preserved

- Ten resolution actions use exact resolution text. Failed resolutions use the
  official introduced text; passed resolutions use House-engrossed text.
- S. 1071 and S. 1318 use House-engrossed amendment (`eah`) text because the
  House action records identify amendments in the nature of a substitute.
- S. 2393 and S. 4465 use Senate-engrossed (`es`) text because the House action
  records show passage without House amendment.
- Failed H.R. 9238 uses the official committee-discharged House (`cdh`) text.
- H.R. 8800 final passage uses the already-governed House Rules Committee final
  text because the Congress.gov endpoint did not yet expose a House-engrossed
  version at the approved cutoff.

One S. 4465 XML Dublin Core title incorrectly says `110`; its canonical
Congress.gov 119th-Congress URL/file identity, exact S. 4465 action record, and
`es` text-version endpoint agree. The independent validator therefore binds
that source through those stronger official identities and does not use the
erroneous Dublin Core number.

## Generic contract and fail-closed behavior

The reusable evaluator contains no member or issue constants. The builder binds
M11B-specific identities outside that evaluator. The closed contract exposes
only six readiness states and deterministic blocker precedence.

Nineteen adversarial tests cover whole-measure readiness, amendment-purpose
readiness, parent-metadata insufficiency, missing operative content, stage
mismatch, later enacted-text substitution, exact-identity mismatch, wrong
amendment/roll binding, missing Clerk evidence, source conflict, raw digest
mismatch, outside-universe rejection, sponsor/cosponsor/party leakage,
vote-direction interpretation leakage, duplicate action records, packet
tampering, and the absence of member/domain constants from the evaluator.

## Validation record

- M11A authority validator: passed.
- M11B deterministic regeneration: passed.
- M11B independent validator: passed at 82 ready / 0 blocked.
- M11B adversarial tests: 19 passed.
- Generic universe-authority and Justice source-readiness regressions: 30
  passed.
- Source-acquisition and packet regressions: 27 passed.
- Justice Semantic IR and full-record regressions: 64 passed; M5 and M5R1
  independent validators passed.
- Documentation and terminology governance, Draft-07/schema validation, 58
  JSON parses, Ruff, format, compilation, and `git diff --check`: passed.
- Exact M11A ancestry and artifact immutability, Justice artifact immutability,
  runtime-diff absence, and protected-ZIP exclusion: passed.

## Authorization boundary

All action-interpretation, episode, Semantic IR, synthesis, public-wording,
publication, and production-persistence flags remain false. Justice remains the
publication-active production reference. No frontend/backend runtime behavior
changed, and no database, publication, production, or deployment write was
performed.
