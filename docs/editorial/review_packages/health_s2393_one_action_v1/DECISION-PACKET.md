# Proposed one-action Health interpretation pilot

Prepared 19 October 2026. Decision status: **unfilled**. This is a proposed bounded interpretation/integration pilot, not a representative Health record, approved content, or publication authorization. No candidate flags or repository artifacts were changed.

## The proposed decision

Consider whether to take one already independently audited action through the governed acceptance workflow: House roll 180, 119th Congress, second session; S.2393; 20 May 2026; “On Motion to Suspend the Rules and Pass.” The House passed the question 405–5, with 20 Not Voting. This small, self-contained authorization is a useful integration pilot because its two member observations exercise both directional support and nondirectional accounting. Its selection makes no claim about typical Health policy or either member’s overall record.

The proposed bounded scope contains exactly one action, one singleton episode, and one Foushee finding. Massie has a resolved Not Voting observation and no directional finding. Existing candidate files use broader full-record compiler scope; this packet does not convert them into a governed bounded-partial public artifact. That conversion, validation, acceptance and later release remain distinct work.

## Exact proposed public copy for owner review

Scope label: “One reviewed vote on a St. Louis VA facility authorization. This is a bounded sample, not an assessment of the member’s overall Health record.”

Finding title: “St. Louis VA facility authorization”

Foushee finding: “On May 20, 2026, Valerie Foushee voted Yea on passing S.2393, which would authorize a St. Louis VA bed tower and clinical expansion, together with administrative, warehouse, utility and parking construction, at a maximum project amount of $1,762,668,000. The bill separately authorizes appropriations for fiscal year 2026 or the year funds are appropriated. It does not itself appropriate the money or establish that construction or care was delivered.”

Massie receipt/accounting text: “Thomas Massie was recorded as Not Voting on this question. That record does not establish support or opposition to the authorization.”

Required detail/qualifications: “This interpretation concerns the House suspension-and-passage vote on the Senate-engrossed text, not a claim of enactment. The bill’s printed short title says fiscal year 2025, while its operative project and appropriation-authorization provisions say fiscal year 2026. The project combines clinical and nonclinical construction. The vote establishes no general veteran benefit, patient-admission rule, guaranteed construction date, or medical outcome. No motive or preferred alternative is inferred.”

This wording is newly proposed here, with ordinary spacing and the exact dollar amount. It is not the previously audited compact string and has no independent public-wording approval. The unchanged audited compact, detail, qualifications and source map are preserved in slice-evidence.json under generated/readable_candidates.json. An owner can request revision rather than accept this proposal.

## Evidence and interpretation

- Action: house:119:2:180. Meaning reference: house119-through-2026-09-16:house:119:2:180:candidate-v1.
- Episode: episode:s2393:119. No parent-package inference, policy family, trait, linked additional action or blocked episode is required by this slice.
- Foushee F000477: Yea → supports_exact_choice; proposition prop:75edca987585935c.
- Massie M001184: Not Voting → resolved_non_directional; excluded from behavioral evidence; no proposition.
- Proposed Health membership rests on the defined VA bed-tower/clinical expansion, preserving the mixed administrative/site scope. Membership remains proposed.
- Shared action core seal: 7df0c99b81ac06d558a9a6906202b25993e3f38eb9fe9a9421fd3c827e95e3e5.
- Action-mapping seal: 5ac6e6b24ab126d19781245af2b2f4f8e80104585d2bab061fe9628097c423a3.

### Source 1: the exact House question and member observations

[House Clerk roll 180](https://clerk.house.gov/evs/2026/roll180.xml). Repository source_id clerk:119:2:180; sources.json pointer /sources/1687. Locators: metadata vote-question, vote-result, action-date; member_records/F000477 and member_records/M001184; party_totals. Raw source SHA-256: cdcf9b4380ba0f7daae98c341396bea2407bf587f4b8994b28a77f45c897895b. Governed source-object seal: eb88c63efbc5d13d03dcf1107601a087a1049e141679d10d89718e30331fd83f.

### Source 2: the complete Senate-engrossed bill

[S.2393 ES](https://www.govinfo.gov/content/pkg/BILLS-119s2393es/html/BILLS-119s2393es.htm). Source_id govinfo:s2393es; sources.json pointer /sources/1705. The prior audit read the complete 1,736-character governed capture. Raw SHA-256: 529db2fc830de6b0d199418962d52867c7de1d17738b80518158155721b5e757. Governed source-object seal: 144cf0e5cc200e45790954355bcd42e45a247eee3ef64faba0d5e01beccec203.

Section 2(a): “The Secretary of Veterans Affairs may carry out a major medical facility project in fiscal year 2026 in St. Louis, Missouri, that consists of the construction of a new bed tower, clinical building expansion, consolidated administrative building and warehouse, utility plant, and parking garages, in an amount not to exceed $1,762,668,000.”

Section 2(b): “There is authorized to be appropriated to the Secretary of Veterans Affairs for fiscal year 2026 or the year in which funds are appropriated for the Construction, Major Projects account, $1,762,668,000 for the project authorized in subsection (a).”

Section 1 prints “Fiscal Year 2025 Veterans Affairs Major Medical Facility Authorization Act”. Complete captured text is included in slice-evidence.json. Governed hashes seal canonical source objects, not just the quoted text; raw hashes are recorded provenance, not newly downloaded official-byte checks.

## Frozen checkpoints and dependency comparison

Freshly verified main: [d61146f7cd6055d6ad4b74979bcb575d7b40c97b](https://github.com/dhart54/political_fingerprint/commit/d61146f7cd6055d6ad4b74979bcb575d7b40c97b), including PR235. Comparison: [PR198 head 51211e8ec2fac3152380e705d8c1646b47047dc0](https://github.com/dhart54/political_fingerprint/commit/51211e8ec2fac3152380e705d8c1646b47047dc0).

Full bytes of eleven candidate files at both commits were downloaded and verified against Git tree blob identities. All 20 selected dependency records match exactly: both source captures, authoring and claim map, membership review, universe disposition, core meaning and source seals, both member projections, compiler inputs, singleton episode/mapping, compiled proposition and nondirectional accounting, readable outputs, and per-action reuse proof. Whole Health files do differ; those unrelated changes are not accepted by this comparison. Parent-envelope candidate restrictions and scope metadata remain unchanged. No hidden source or additional action reference was found in this interpretation’s closure.

The seven generation-rule files named by the saved reproducibility proof have identical Git blobs across the two heads. Their current canonical-string hashes also match the saved proof. Local checks recomputed both governed-source seals and the action-core seal, and verified that the complete bound bill passage equals its captured source text. These are integrity/consistency checks, not a new full pipeline replay or independent semantic audit.

The unchanged [Health audit](https://github.com/dhart54/political_fingerprint/blob/d61146f7cd6055d6ad4b74979bcb575d7b40c97b/docs/review_packets/health_semantic_audit_7d53914.json) reconstructed this complete source, checked exact choice, membership, qualifications, singleton episode, both member outputs and source binding. It recorded a MAJOR shared/member-leakage correction, AUDIT-SHARED-MEMBER-CHOICES, as corrected. The current slice preserves the corrected separation. Reusing that audit does not accept the full 115-action Health candidate. PR198’s candidate-only merge remains a separate decision and does not confer acceptance on this slice.

## Owner decision fields (intentionally blank)

- Bounded pilot scope and selection accepted, revised, or declined: __________
- Exact shared meaning and listed qualifications accepted, revised, or declined: __________
- Health membership and singleton episode accepted, revised, or declined: __________
- Foushee finding wording and Massie nondirectional accounting accepted, revised, or declined: __________
- Requested revisions or additional independent review: __________
- Decision-maker, date, exact packet/checkpoint binding: __________

These fields are a discussion aid, not a fabricated positive receipt. Any eventual acceptance must be recorded through the governing content-bound workflow at its precise layer. Acceptance of meaning does not automatically approve episode/IR/public wording, storage, activation, or deployment. Publication and production writes are not requested or authorized by this packet.

## Remaining gates and limitations

The evidence closure is established for this candidate interpretation and the two frozen heads. It is not a claim that an extracted one-action release bundle currently exists or passes the bounded-partial public compiler. The newly proposed public copy still needs review. No live sources were recaptured, no current legislative outcome beyond the recorded House question was inferred, no browser rendering was tested, and no production state was changed. If a newer source or material dependency changes, review only that affected closure before binding a decision.

Governance: AGENTS.md and docs/workflows/codex-operating-model.md distinguish candidates from acceptance; docs/methodology/full_record_issue_interpretation_v1.md defines bounded_partial_record and limits full-record synthesis; docs/plans/m11d_national_security_action_meaning_acceptance_v1.md demonstrates content-bound, layer-specific human acceptance. The existing shared-candidate persistence/public-authoring guard remains in force.

Files: slice-evidence.json contains exact objects and JSON pointers; slice-comparison.json records file-level Git identities and slice equality; audit-excerpt.json preserves the prior scoped review; rule-verification.json distinguishes raw-file hashes from canonical proof hashes; local-validation.json records checks. None is an acceptance receipt.
