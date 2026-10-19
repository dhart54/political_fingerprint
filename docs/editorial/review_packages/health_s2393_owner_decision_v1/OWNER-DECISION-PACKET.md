# S.2393 Health: pending owner decision packet

Decision status: **pending; no new approval recorded**.

This is an inert documentary decision subject and worksheet, accompanied by the existing typed IR review payload. It is **not an executable formal acceptance-chain subject**. `approval_conferred=false`; executable acceptance-chain admission is unresolved.

Review scope: `bounded_partial_record`. Exactly `house:119:2:180`, singleton `episode:s2393:119`, F000477 and M001184. This does not assess either member's complete Health record. Compiler `case_scope=full_record` accounts for supplied inputs only.

Bundle decision: __________  Reviewer: __________  Reviewed at (UTC): __________

An owner may accept, request revision or reject the exact documentary subject below. This blank worksheet records no decision. A later decision must identify this exact subject and its limits; it does not execute acceptance, production eligibility, storage or publication.

## Prior decision and current subject

The [earlier documentary receipt](../../../review_packets/health_one_action_owner_decision_receipt_draft.md) records Dylan's 19 October 2026 Accept for selection/scope, exact interpretation and qualifications, Health membership/singleton episode, and exact packet wording/accounting. That decision does not accept this new graph, review payload or mapping implementation. Original historical blank fields remain unchanged.

The [original packet](../health_s2393_one_action_v1/DECISION-PACKET.md) SHA-256 remains `3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`. Original ZIP remains **unverified**. Original normalized Health sources and hashes remain unchanged; no fresh acquisition or archive authentication is claimed.

Pinned input Git origin: `a0605e4e3e3a81751bf273155f1cf5e0cfa4d21a` (PR237 merge). Full compiled IR canonical subject SHA-256: `29be897f6a2d48754f2ac5ec5966474cad88ba0bed9df36cb654af2fa9b4ace6`. The [review payload](review_payload.json) binds that entire IR, including both members; its approval flag remains false.

## Complete two-member disposition and pending decisions

| Member | Official action | Candidate disposition | Owner decision |
|---|---|---|---|
| F000477 (Foushee) | Yea | Exact-choice support; one notable choice `prop:75edca987585935c`; singleton `episode:s2393:119` | Pending |
| M001184 (Massie) | Not Voting | Resolved nondirectional; zero behavioral propositions; `non_directional_status` accounting | Pending |

Foushee's existing `conclusion_relevance=supporting` and `presentation_target=other_notable_choices` are preserved. No relabeling to `primary`, full-issue synthesis or extra proposition is proposed. Massie is neither opposition nor missing evidence. His accounting mapping retains the actual Not Voting boundary and no episode IDs.

### F000477: exact candidate objects

```json
{
  "action_accounting": {
    "behavioral_proposition_action_ids": [
      "house:119:2:180"
    ],
    "non_proposition_reasons": []
  },
  "coverage": {
    "complete_episodes": 1,
    "context_only_control_actions": 0,
    "directional_yes_no_positions": 1,
    "eligible_substantive_actions": 1,
    "in_service_eligible_actions": 1,
    "missing_evidence_actions": 0,
    "not_voting_actions": 0,
    "outside_service_actions": 0,
    "partial_episodes": 0,
    "present_actions": 0,
    "resolved_eligible_actions": 1,
    "unresolved_service_actions": 0
  },
  "proposition_graph": {
    "propositions": [
      {
        "conclusion_relevance": "supporting",
        "direction": "support",
        "evidence_action_ids": [
          "house:119:2:180"
        ],
        "evidence_episode_ids": [
          "episode:s2393:119"
        ],
        "mechanism_or_trait_refs": [],
        "presentation_target": "other_notable_choices",
        "proposition_id": "prop:75edca987585935c",
        "proposition_type": "notable_choice",
        "relationships": {
          "limited_by": [],
          "supported_by": []
        },
        "semantic_role": "behavioral"
      }
    ]
  }
}
```

### M001184: exact candidate objects

```json
{
  "action_accounting": {
    "behavioral_proposition_action_ids": [],
    "non_proposition_reasons": [
      {
        "action_id": "house:119:2:180",
        "detail": "The action is explicitly excluded from behavioral evidence.",
        "reason_code": "non_directional_status"
      }
    ]
  },
  "coverage": {
    "complete_episodes": 1,
    "context_only_control_actions": 0,
    "directional_yes_no_positions": 0,
    "eligible_substantive_actions": 1,
    "in_service_eligible_actions": 1,
    "missing_evidence_actions": 0,
    "not_voting_actions": 1,
    "outside_service_actions": 0,
    "partial_episodes": 0,
    "present_actions": 0,
    "resolved_eligible_actions": 1,
    "unresolved_service_actions": 0
  },
  "proposition_graph": {
    "propositions": []
  }
}
```

## Seven unchanged presentation records

All exact text, qualifications and complete mapping objects below are preserved from the reviewed candidate. They are typed review fragments, not a compiled public presentation. The complete original presentation-input file is separately hash-bound.

### F000477 / finding

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:F000477:finding",
    "presentation_target": "other_notable_choices",
    "proposition_ids": [
      "prop:75edca987585935c"
    ],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:F000477:finding",
  "text": "On May 20, 2026, Valerie Foushee voted Yea on passing S.2393, which would authorize a St. Louis VA bed tower and clinical expansion, together with administrative, warehouse, utility and parking construction, at a maximum project amount of $1,762,668,000. The bill separately authorizes appropriations for fiscal year 2026 or the year funds are appropriated. It does not itself appropriate the money or establish that construction or care was delivered."
}
```

### F000477 / finding_title

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:F000477:finding_title",
    "presentation_target": "other_notable_choices",
    "proposition_ids": [
      "prop:75edca987585935c"
    ],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:F000477:finding_title",
  "text": "St. Louis VA facility authorization"
}
```

### F000477 / qualifications

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [
      "scope:s2393-review:f000477"
    ],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:F000477:qualifications",
    "presentation_target": "scope_note",
    "proposition_ids": [],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:F000477:qualifications",
  "text": "This interpretation concerns the House suspension-and-passage vote on the Senate-engrossed text, not a claim of enactment. The bill’s printed short title says fiscal year 2025, while its operative project and appropriation-authorization provisions say fiscal year 2026. The project combines clinical and nonclinical construction. The vote establishes no general veteran benefit, patient-admission rule, guaranteed construction date, or medical outcome. No motive or preferred alternative is inferred."
}
```

### F000477 / scope_label

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [
      "scope:s2393-review:f000477"
    ],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:F000477:scope",
    "presentation_target": "scope_note",
    "proposition_ids": [],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:F000477:scope",
  "text": "One reviewed vote on a St. Louis VA facility authorization. This is a bounded sample, not an assessment of the member’s overall Health record."
}
```

### M001184 / accounting

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [
      "coverage:c9ecb27beef8637e"
    ],
    "episode_ids": [],
    "mapping_id": "mapping:s2393-review:M001184:accounting",
    "presentation_target": "coverage_note",
    "proposition_ids": [],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:M001184:accounting",
  "text": "Thomas Massie was recorded as Not Voting on this question. That record does not establish support or opposition to the authorization."
}
```

### M001184 / qualifications

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [
      "scope:s2393-review:m001184"
    ],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:M001184:qualifications",
    "presentation_target": "scope_note",
    "proposition_ids": [],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:M001184:qualifications",
  "text": "This interpretation concerns the House suspension-and-passage vote on the Senate-engrossed text, not a claim of enactment. The bill’s printed short title says fiscal year 2025, while its operative project and appropriation-authorization provisions say fiscal year 2026. The project combines clinical and nonclinical construction. The vote establishes no general veteran benefit, patient-admission rule, guaranteed construction date, or medical outcome. No motive or preferred alternative is inferred."
}
```

### M001184 / scope_label

```json
{
  "mapping": {
    "action_ids": [
      "house:119:2:180"
    ],
    "boundary_ids": [
      "scope:s2393-review:m001184"
    ],
    "episode_ids": [
      "episode:s2393:119"
    ],
    "mapping_id": "mapping:s2393-review:M001184:scope",
    "presentation_target": "scope_note",
    "proposition_ids": [],
    "receipt_refs": [
      "docs/review_packets/health_one_action_owner_decision_receipt_draft.md"
    ],
    "source_refs": [
      "clerk:119:2:180",
      "govinfo:s2393es"
    ]
  },
  "statement_id": "statement:s2393-review:M001184:scope",
  "text": "One reviewed vote on a St. Louis VA facility authorization. This is a bounded sample, not an assessment of the member’s overall Health record."
}
```

## Exact frozen input identities

Hashes below are actual pinned Git blob bytes, independent of working-checkout CRLF conversion. JSON objects are also compared in full with those pinned inputs. No original input is rewritten.

| Input (in original package) | Git blob | Raw Git bytes SHA-256 |
|---|---|---|
| [DECISION-PACKET.md](../health_s2393_one_action_v1/DECISION-PACKET.md) | `18ad34ad4f8ea2fd09cbdcba80d5ecd7a96e4584` | `3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347` |
| [shared_action_core.json](../health_s2393_one_action_v1/shared_action_core.json) | `be11cc190b23c574d9b902d601a9359a4eea0c61` | `cf9dd618381d230c480bfcef271992ad33efabb7558365ee05a121aebdb0bd2b` |
| [shared_issue_mapping.json](../health_s2393_one_action_v1/shared_issue_mapping.json) | `6ecbeeb0e8d83244fbb854d78317c14ea2c459ff` | `6b634595ad096ab782cb84e628b368b265688d1a7ed86f20c8469a33a42d1b28` |
| [member_projections.json](../health_s2393_one_action_v1/member_projections.json) | `b1fb4ae252d160e53fd9db42836931efc57245c3` | `8e2949a2bb70b674e2407c9a196681b9362ec8561d72b7ec21aa80baf7be8066` |
| [governed_sources.json](../health_s2393_one_action_v1/governed_sources.json) | `aef56b33973eea91a8c1b5c3e7ca66f804abaac4` | `833769acb7c57afe9f9404bb581955e9a12f6f98d4a00e462ef5b6fc8641efdf` |
| [claim_source_map.json](../health_s2393_one_action_v1/claim_source_map.json) | `df2d696f0ed43ea01f68ff06ae2494f3738ec152` | `f7e602de6ff73632cfe0c7cc63b395db50ea8d5e6e76ceb95714ba25493135ef` |
| [membership_evidence.json](../health_s2393_one_action_v1/membership_evidence.json) | `9daffe37a60687432d9b97ba1446773ef5c12267` | `5061cfef3bbadceda0599f2199d3b6aeb745811391636283455b272ff3aa4b21` |
| [compiler_input.json](../health_s2393_one_action_v1/compiler_input.json) | `60bf32c62370ade4648b63690a2189da2d50749e` | `e40781706fb9d0c7467376286c1b3e9221dbd81d96d6261c99e83b1e980f2a9f` |
| [compiled_ir.json](../health_s2393_one_action_v1/compiled_ir.json) | `f5f92d563362eaf078f093db58222faf3a0915c3` | `efd83816e61ca2de516e734c0b2da87a81202d95dd2abcda411605f8f83e773c` |
| [presentation_payload.json](../health_s2393_one_action_v1/presentation_payload.json) | `d87b0cb0b1b9e3bd73807f8bb5642d85fdb416b2` | `a9d7c685f04b4d78e366559c32ca3354b774d2e92e5699028d3e51b93b4515ec` |
| [presentation_inputs.json](../health_s2393_one_action_v1/presentation_inputs.json) | `6aecfc851d816eac5a229c0fbbd1bce4f140c868` | `c52e5773f6b0ad518c4b5f5697a98587308702588131060c17099358c022b7a2` |
| [review_source_contract.json](../health_s2393_one_action_v1/review_source_contract.json) | `c2d0a07b4df1492e90daf74d9e639dda194fee48` | `e7304b1a97c8aee7b23b64baf87e7fc6c433c65a7d6a34def07488e312391a53` |
| [provenance.json](../health_s2393_one_action_v1/provenance.json) | `3a5cd81ec5ea6820968debaa4d08847b99fbb891` | `030f8a2d6d1ba85a52696ca63ad00fc6827f6ef9453a7c119b34115c4b6ba4fa` |

## Additional retained raw preparation evidence

The following existing raw objects are read from pinned Git origin `a0605e4e3e3a81751bf273155f1cf5e0cfa4d21a`, validated by their actual SHA-256, parsed and checked for S.2393 ES provisions, roll180 member observations and the recorded House suspension/pass stage. These are **additional preparation evidence only**. Their historical National Security acceptance, issue membership and episode identity do not transfer. They do not replace the original normalized Health sources, their different recorded raw hashes, source maps or governed-object seals. Later entries in the raw actions feed add no claim to this bounded packet.

- Existing source identity `congress-text:119:s:2393:es`: `docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/04f063befa42e8b335fc14539b218401408cfb806c3e734438a67d944db10689_BILLS-119s2393es.xml`; SHA-256 `04f063befa42e8b335fc14539b218401408cfb806c3e734438a67d944db10689`; Git blob `5edbac307815d6a05aa1b311195e808649d44ff0`.

- Existing source identity `clerk:house:119:2:180`: `docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/d52d940529fbb4eab886c5c32ad6e712097829f93c886d5adb8cd171541c5e52_roll119_2_180.xml`; SHA-256 `d52d940529fbb4eab886c5c32ad6e712097829f93c886d5adb8cd171541c5e52`; Git blob `04a903cf0d1d7d1cbf3bfa749862d0f006ccef22`.

- Existing source identity `congress-actions:house:119:2:180`: `docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/a143f675f626923c67e3b3b50b242be832f4daab6389caed725b3f70ccef7bc0_119_s_2393_actions.json`; SHA-256 `a143f675f626923c67e3b3b50b242be832f4daab6389caed725b3f70ccef7bc0`; Git blob `fbddc32971c5e94983390806b0a3bc0103bb7a6e`.

## Executable admission remains unresolved

The optional full-record receipt requires `review_scope=full_defined_issue_record` and `decision=approved_complete_issue_universe`. Those constants are incompatible with this bounded pilot. This packet carries no such receipt and makes no full-universe claim. A schema-valid null decision fragment is not proof of complete acceptance-chain admission.

No Health full-record source-readiness/candidate/evidence-map/decision-template chain, accepted action implementation, accepted policy-episode implementation, or opt-in behavioral candidate envelope is asserted. Required missing artifact IDs and hashes are not fabricated. No National Security authority is substituted. The [admission report](../../../review_packets/health_one_action_acceptance_admission_report.md) identifies exact contracts, evidence requirements, alternatives and limits.

The existing pipeline, public compiler and persistence guards remain intact. Completing this documentary review does not accept/promote a graph, authorize public authoring, approve a release artifact, confer benchmark/production eligibility, change a runtime manifest, write a database or publication registry, or deploy. Any later executable acceptance path must first resolve its applicable bounded admission and truthful content-bound prerequisites under separately applicable authority.
