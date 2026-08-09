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
  as pre-floor contextual provenance for final passage.

M11B added 186 unique content-addressed raw files totaling 23,375,949 bytes.
The artifact references those files plus one pre-existing governed Rules
Committee PDF, for 187 unique governed raw paths totaling 26,447,188 bytes.
Raw official provenance is separate from the closed neutral source projections.

The 214 source bindings comprise 82 Clerk rolls, 50 exact Congress.gov action
lists, 49 Congress.gov operative XML texts, 32 exact amendment-index bindings,
and one pre-floor Rules report context. Role accounting contains 82
member-action bindings, 131 exact identity/stage bindings, and 82 attempted
operative-content bindings. The Rules report is not an identity/stage binding
and its attempted operative binding fails the final-stage criteria.

Readiness result:

- `81` `ready_for_action_interpretation`
- `1` `blocked_stage_mismatch`: `house:119:2:278`
- artifact identity:
  `interpretation-source-readiness:f000477:national_security_foreign:119:v1`
- artifact file digest:
  `acfd656ccce57e8ef0668bcedeb5c51b0ea6342097310db13236ffc5d16bf86c`
- source-readiness subject digest:
  `53af365c4b06d4cc96fdeba17a1d65c80d89ae960d8cf986b7a5bf9599ec51bd`

## Stage edge cases mechanically preserved

- Ten resolution actions use exact resolution text. Failed resolutions use the
  official introduced text; passed resolutions use House-engrossed text.
- S. 1071 and S. 1318 use House-engrossed amendment (`eah`) text because the
  House action records identify amendments in the nature of a substitute.
- S. 2393 and S. 4465 use Senate-engrossed (`es`) text because the House action
  records show passage without House amendment.
- Failed H.R. 9238 uses the official committee-discharged House (`cdh`) text.
- A fresh August 9, 2026 official-source check found only `IH` and `RH` for
  H.R. 8800 in Congress.gov; its direct `EH` URL was absent. GovInfo search
  likewise exposed only `RH`, and the apparent `EH` content URL returned a
  GovInfo page-not-found HTML document rather than legislative XML. The July 20
  Rules report is therefore retained only as pre-floor context. Because it
  precedes later floor amendment dispositions and engrossment instructions,
  roll 278 fails closed as `blocked_stage_mismatch` rather than using the
  context document as final-passage operative content.
- H.R. 2721 remains ready on its exact `EH` text and canonical September 16,
  2025 action date. Its material limitation records Congress.gov's source-native
  `(text: 09/16/2026 CR H4286)` parenthetical discrepancy without allowing that
  description to override the Clerk/actionDate evidence.

One S. 4465 XML Dublin Core title incorrectly says `110`; its canonical
Congress.gov 119th-Congress URL/file identity, exact S. 4465 action record, and
`es` text-version endpoint agree. The independent validator therefore binds
that source through those stronger official identities and does not use the
erroneous Dublin Core number.

## Generic contract and fail-closed behavior

The reusable evaluator contains no member or issue constants. The builder binds
M11B-specific identities outside that evaluator. The closed contract exposes
only six readiness states and deterministic blocker precedence.

Twenty-four adversarial tests cover whole-measure readiness, amendment-purpose
readiness, parent-metadata insufficiency, missing operative content, stage
mismatch, later enacted-text substitution, exact-identity mismatch, wrong
amendment/roll binding, missing Clerk evidence, source conflict, raw digest
mismatch, outside-universe rejection, sponsor/cosponsor/party leakage,
vote-direction interpretation leakage, duplicate action records, packet
tampering, the absence of member/domain constants from the evaluator, pre-floor
Rules-report rejection even when renamed as final text, exact `EH` acceptance,
source-native descriptive-date isolation, and preservation of the other 81
ready actions.

## Validation record

- M11A authority validator: passed.
- M11B deterministic regeneration: passed.
- M11B independent validator: passed at 81 ready / 1
  `blocked_stage_mismatch`.
- M11B adversarial tests: 24 passed.
- Generic universe-authority and Justice source-readiness regressions: 30
  passed.
- Source-acquisition and packet regressions: 27 passed.
- Justice Semantic IR and full-record regressions: 64 passed; M5 and M5R1
  independent validators passed.
- Documentation and terminology governance, Draft-07/schema validation, 58
  JSON parses, Ruff, format, compilation, and `git diff --check`: passed.
- Exact M11A ancestry and artifact immutability, Justice artifact immutability,
  runtime-diff absence, and protected-ZIP exclusion: passed. All 81 actions
  other than corrected roll 278 retain their prior readiness state; H.R. 2721
  changes only by the mandated material limitation.

## Authorization boundary

All action-interpretation, episode, Semantic IR, synthesis, public-wording,
publication, and production-persistence flags remain false. Justice remains the
publication-active production reference. No frontend/backend runtime behavior
changed, and no database, publication, production, or deployment write was
performed.
