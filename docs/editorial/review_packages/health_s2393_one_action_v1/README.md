# S.2393 one-action Health review package

This is an inert candidate review package for `house:119:2:180`, S.2393, and
singleton `episode:s2393:119`. It contains one Foushee Yea support proposition and
Massie's resolved nondirectional Not Voting accounting. It makes no overall
Health-record or full-issue synthesis claim. New generated artifacts are
**unapproved, non-public, not production eligible and not persistence eligible**.

The exact [packet](DECISION-PACKET.md) has SHA-256
`3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`.
Its historical blank decision fields remain unchanged. The separate
[owner decision receipt](../../../review_packets/health_one_action_owner_decision_receipt_draft.md)
records the later reported Accept and its exact layers; it does not accept this
new IR or these newly mapped review inputs. The source route was a supported
plaintext handoff. **The original ZIP remains unverified and unopened.** Local
Git extraction is independently recorded provenance and does not establish ZIP
identity. Official bytes were not recaptured from the network.

## Files and contract boundaries

| Files | Role and validation |
| --- | --- |
| `shared_action_core.json`, `shared_issue_mapping.json`, `member_projections.json` | Existing Shared Legislative Corpus V1 types and validators. Core and projection collection IDs use the existing issue-neutral numeric `v4` revision syntax; the individual action/meaning/source seals stay unchanged. This review revision is not a canonical production version or identity reservation. |
| `governed_sources.json`, `claim_source_map.json` | Exact selected governed source objects and complete bound 1,736-character Senate-engrossed bill passage. The Clerk capture retains its stored two member rows, metadata, party totals and governed seal; it is not a newly downloaded full XML file. |
| `membership_evidence.json` | Unchanged selected prior membership-review record, preserving the direct clinical-infrastructure rationale and mixed administrative/site scope. Its original claim-map reference resolves within the pinned upstream authoring file, not this directory. |
| `compiler_input.json`, `compiled_ir.json` | One-action candidate input through the existing corpus adapter and `run_editorial_pipeline`; existing structural IR validation. Compiler `case_scope=full_record` accounts for all supplied inputs, not the complete Health universe. Issue review scope remains `bounded_partial_record`. |
| `presentation_payload.json` | Existing candidate presentation adapter output selecting compiled objects without new analysis. It is not a public presentation. |
| `presentation_inputs.json` | Seven mapped review text fragments using existing `analyticalText`/`mapping` definitions and semantic-reference validation. Exact packet scope label, title, Foushee finding, Massie accounting and qualifications are preserved literally. Scope/qualification fragments use scope boundaries; Massie accounting uses its actual compiled Not Voting boundary and no proposition. |
| `review_source_contract.json` | Existing `editorial_action_source_contract_v1` shape, independently derived from pinned governed sources and claim bindings for review validation only. No production authority or canonical source binding is established. |
| `provenance.json` | Documentary scope, upstream Git blob/file hashes, seven unchanged generation-rule hashes and preparation-tool hash, packet route, decision references, negative authority and generated-byte hashes. It is not a new storage contract. |

The presentation inputs are typed fragments, **not a complete public-authoring
document or public artifact**. No public compiler is invoked successfully. Tests
confirm that the existing candidate guards reject both these inputs and this IR
at public-authoring/public-compilation and persistence boundaries. No candidate
flag is removed or promoted to make a preview or storage payload possible.

## Reproduce and validate

Run from the repository root with the pinned local Git commits available:

```powershell
python scripts/prepare_health_one_action_review.py --check
python -m unittest backend.tests.test_health_one_action_review -v
python scripts/validate_editorial_semantic_ir.py
```

Without `--check`, the preparation command writes only its twelve named JSON
outputs in this directory. It reads the packet as exact bytes and fails on any
hash mismatch, including checkout newline conversion; it never normalizes a
changed packet to fit the expected identity. Packet blob bytes in Git are the
original LF UTF-8 bytes. `--check` compares generated JSON objects without writing;
JSON text checkout newline differences do not imply semantic drift. Generated
file hashes describe the preparation tool's UTF-8/LF serialization.

The focused suite covers wording/packet parity, singleton/source closure,
Foushee/Massie distinctions, membership, immutability, deterministic regeneration,
scope/source/action/episode/proposition/boundary mutations, candidate promotion
attempts, all existing candidate refusal paths, and historical seed identity
refusal. The module is selected in the existing hosted `m14h-exact-head` job's
“Validate shared candidate preparation at exact head” pytest invocation, alongside
the shared-domain and shared-corpus tests. That job checks out the PR head with
full Git history. The review correction changes only this test list; workflow
permissions, secrets, environments, triggers and deployment behavior are unchanged.

## Remaining gates

No database, importer, persistence proposal, environment file, runtime manifest,
publication registry, frontend integration or manual deployment is touched.
Automatic PR previews may build the existing application; they do not display
or validate this package. No browser rendering is claimed. The successor PR
remains a draft and may not be merged under this milestone.

Later work requires content-bound review of these exact new artifacts, any
required full public-authoring implementation and representability decisions,
and an established compatible storage path before disposable validation. The
historical seed importer is not a Health importer. Storage-contract changes,
new artifact acceptance and product publication remain separate decisions.
