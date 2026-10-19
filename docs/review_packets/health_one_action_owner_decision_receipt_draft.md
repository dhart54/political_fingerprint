# Health one-action owner decision receipt — documentary draft

Status: documentary draft for repository review, 19 October 2026. This records the
reported human decision against exact packet content. It is not an executable
authority artifact, an accepted IR bundle, a storage contract, or a publication
receipt. No candidate status is changed by this document.

## Detached decision and packet binding

- Decision-maker: Dylan, as identified by the supplied decision relay.
- Decision: `Accept`, confined to the four packet decision layers below.
- Decision timestamp: `2026-10-19T16:57:50Z`.
- Message reference: `messageSentinel_b43433d9493081918ba2101e97dac6e3`.
- Request reference: `requestSentinel_94f29fc5c1f481919ff69134613a60a5`.
- Source chat: `01a15000-0ff6-73e2-95ac-fe6aee80201f`.
- Decision provenance: supplied supported textual relay of the verified Accept;
  the original human turn was not independently reopened in this desktop task.
- Exact packet SHA-256:
  `3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`.
- Local packet file: `.tmp/health-one-action-local-preparation/DECISION-PACKET.md`
  (not included in this two-document PR).
  The supplied plaintext was saved as UTF-8 without BOM, LF, exactly one final
  newline, and independently hashed. Its original `unfilled` status and blank
  decision fields remain unchanged. This later decision is recorded separately.
- Packet Library identity, supplied as metadata only:
  `libfile_8f53bd39a90081919f705f12f17c1ce0`. No Library download is claimed.
- Evidence ZIP: **UNVERIFIED, not delivered or opened**. Supplied identity:
  `libfile_7ff73ceed7f08191aad3ba60336ef29d`; expected SHA-256 only:
  `92e8e77beb8c25758da10bcbe9c744c5ed23079d105abaa1180b75c576f26fce`.

## Precise decision envelope

The reported Accept binds these packet layers as written; it does not accept
the 115-action Health candidate, its broader universe, or generated artifacts
as a whole.

| Accepted editorial layer | Exact bounded subject |
| --- | --- |
| Pilot scope and selection | One action `house:119:2:180`, S.2393, House suspension and passage on 20 May 2026; one singleton episode `episode:s2393:119`; one Foushee finding and Massie accounting only. |
| Exact shared meaning and qualifications | Defined St. Louis VA project authorization, maximum $1,762,668,000; separate authorization of appropriations; mixed clinical and administrative/site construction; printed FY2025 title versus operative FY2026; House question does not establish enactment, appropriation, expenditure, construction or delivered care. Preserve all packet qualifications and source bindings. |
| Health membership and episode | Clinical bed-tower/expansion basis with mixed project scope preserved; singleton S.2393 episode only; no parent-package inference, policy family, trait, other action, or issue-wide position. |
| Member wording and accounting | Exact packet Foushee wording below; F000477 Yea supports the exact choice. M001184 Not Voting is resolved nondirectional, creates no directional finding, and is excluded from support/opposition. |

The acceptance covers packet wording rather than replacing it with the older
audited compact string. The historical packet continues to describe that wording
as proposed; the later Accept supplies the separately recorded editorial decision.
No revision was supplied in the relay. Any changed text, source version, action
set, membership, episode, or material dependency needs a separately bound review
of the affected layer. No acceptance extends to unseen ZIP bytes.

## Exact packet wording bound by the decision

Scope label: “One reviewed vote on a St. Louis VA facility authorization. This is a bounded sample, not an assessment of the member’s overall Health record.”

Finding title: “St. Louis VA facility authorization”

Foushee finding: “On May 20, 2026, Valerie Foushee voted Yea on passing S.2393, which would authorize a St. Louis VA bed tower and clinical expansion, together with administrative, warehouse, utility and parking construction, at a maximum project amount of $1,762,668,000. The bill separately authorizes appropriations for fiscal year 2026 or the year funds are appropriated. It does not itself appropriate the money or establish that construction or care was delivered.”

Massie receipt/accounting text: “Thomas Massie was recorded as Not Voting on this question. That record does not establish support or opposition to the authorization.”

Required detail/qualifications: “This interpretation concerns the House suspension-and-passage vote on the Senate-engrossed text, not a claim of enactment. The bill’s printed short title says fiscal year 2025, while its operative project and appropriation-authorization provisions say fiscal year 2026. The project combines clinical and nonclinical construction. The vote establishes no general veteran benefit, patient-admission rule, guaranteed construction date, or medical outcome. No motive or preferred alternative is inferred.”

## Independent local Git evidence binding

Pinned main and locally observed `origin/main`:
`d61146f7cd6055d6ad4b74979bcb575d7b40c97b`.
Comparison head: `51211e8ec2fac3152380e705d8c1646b47047dc0` (PR198).
The initial preparation checkout was at
`9e19099e14dfd7e1ebe163d3d3b2ffc439be86b6`; the delivery branch starts from
pinned main. All relevant working-tree evidence and rule files equal pinned main.

Twenty independently selected dependency records across eleven candidate files
are equal at the pinned commits. Every source file's raw bytes were read with
`git show` and verified against its Git blob identity. These records were selected
from the packet's described closure; they are not the unseen archive's original
selection/comparison manifest. Seven whole files differ, so equality of this
slice cannot confer authority on their unrelated contents. Seven generation-rule
blobs are identical and their canonical-string hashes match the stored proof.

For independent review, the base directory for every path below is
`docs/editorial/shared_candidates/house_119_health_20260916/`, at both
[pinned main](https://github.com/dhart54/political_fingerprint/tree/d61146f7cd6055d6ad4b74979bcb575d7b40c97b/docs/editorial/shared_candidates/house_119_health_20260916)
and [PR198 head](https://github.com/dhart54/political_fingerprint/tree/51211e8ec2fac3152380e705d8c1646b47047dc0/docs/editorial/shared_candidates/house_119_health_20260916).
Read raw files with `git show <commit>:<path>`; resolve the JSON pointers;
canonicalize objects with `json.dumps(value, ensure_ascii=False, sort_keys=True,
separators=(",", ":")).encode("utf-8")` before SHA-256. These hashes include any
existing seal field, unlike the seal values listed separately below.

| File | JSON pointer at both commits | Canonical object SHA-256 |
| --- | --- | --- |
| `sources.json` | `/sources/1687` | `8f950ea1478980ae6aaed47f08ca7087442ff2da473c11d55c78d2b6d8b32f09` |
| `sources.json` | `/sources/1705` | `9724a55494cae6f453a87c358ca674833237472b8313fd7fbec0c44bd108c5d6` |
| `authoring.json` | `/actions/92` | `aaa83938d0cb8c7df7b25938b09d6960bcbf73c1905e5f23a43911b538a3a945` |
| `authoring.json` | `/actions/92/claim_source_map` | `06842839c6e2d30f98fe54b3715dec076d29f2229e3daf585448fef655b68a18` |
| `membership_review.json` | `/records/461` | `cf9b26e72cfb61551dd29f4e02128d93816fb90313e7f93ba614287218669009` |
| `universe_proposal.json` | `/candidate_dispositions/541` | `cdb3223064eb34e3debe3e502b9fc23bf6e1aaf3cd3534aacc9b75e1e6c06735` |
| `generated/shared_action_core.json` | `/actions/92` | `cce06a996567d1824974069441b75b8b13818d509a591d25c4b3e570f34dea99` |
| `generated/shared_issue_mapping.json` | `/action_mappings/92` | `122f804e3eb5581bf793be128ae332e9864f8d4f4a42a323e0856e0c2fb4762e` |
| `generated/shared_issue_mapping.json` | `/episodes/70` | `4afdf597311b6ad1d5ffbeba6dca8bcb3e74565c1884ce3dd096461147020079` |
| `generated/member_projections.json` | `/0/actions/92` | `3f793015210c3da9a777f3e0940f82b386aff79ced4ed3715192ad64f02365b6` |
| `generated/member_projections.json` | `/1/actions/92` | `ecf22441e891ff3ad05de00fd0ab05f0d1ca1a9692e3a32651d6ea8dbb830714` |
| `generated/compiler_input.json` | `/members/0/actions/92` | `cf2943343e4f5f8414cec2565741ea0ce838f783b8007a0f288200ecda6f6cef` |
| `generated/compiler_input.json` | `/members/1/actions/92` | `8c86a35a2753beaa5d76d57c1b8ebebbe0a1ab391ca25a8a048712307cc1c1ff` |
| `generated/compiler_input.json` | `/shared_semantics/actions/92` | `40d26e688537311eca30795ca36d2f94017960251d93fc056850ddd29ed74b97` |
| `generated/compiler_input.json` | `/shared_semantics/episodes/70` | `4afdf597311b6ad1d5ffbeba6dca8bcb3e74565c1884ce3dd096461147020079` |
| `generated/compiled_ir.json` | `/members/0/proposition_graph/propositions/57` | `3cffaa4696962fbf46098f06bc6efbf0a1a691c2a1ee5d57b0460fc3cdeb3775` |
| `generated/compiled_ir.json` | `/members/1/action_accounting/non_proposition_reasons/4` | `8cf0349499143cdcf6dfd3fa342b63fdc38ada36e4676d03bfdcc3f21acfd354` |
| `generated/readable_candidates.json` | `/members/0/findings/57` | `9c0783573b3657d2baf135251d28e001a9da29b21a14acbe061b302d3fe9fb2c` |
| `generated/readable_candidates.json` | `/members/1/non_proposition_accounting/4` | `8cf0349499143cdcf6dfd3fa342b63fdc38ada36e4676d03bfdcc3f21acfd354` |
| `generated/reproducibility_proof.json` | `/real_member_reuse/92` | `f295c79b1194d5f3e72837662142f4fb897992392b8338a5d2c41048c2b29b60` |

The seven rule paths and saved canonical-string hashes are in
`generated/reproducibility_proof.json#/rule_files_sha256`. Those paths are
`scripts/prepare_shared_domain_candidate.py`,
`backend/app/semantic_ir/{shared_corpus,compiler,pipeline,adapters,validation}.py`,
and `docs/semantic_ir/shared_legislative_corpus_v1.schema.json`. Their Git blobs
are identical at both commits; proof hashing applies the same canonical JSON
encoding to each decoded, universal-newline-normalized file string.

| Bound record | Existing seal or canonical object SHA-256 |
| --- | --- |
| Clerk source object | `eb88c63efbc5d13d03dcf1107601a087a1049e141679d10d89718e30331fd83f` |
| Senate-engrossed source object | `144cf0e5cc200e45790954355bcd42e45a247eee3ef64faba0d5e01beccec203` |
| Shared action core | `7df0c99b81ac06d558a9a6906202b25993e3f38eb9fe9a9421fd3c827e95e3e5` |
| Action mapping | `5ac6e6b24ab126d19781245af2b2f4f8e80104585d2bab061fe9628097c423a3` |
| Membership record | `cf9b26e72cfb61551dd29f4e02128d93816fb90313e7f93ba614287218669009` |
| Singleton episode | `4afdf597311b6ad1d5ffbeba6dca8bcb3e74565c1884ce3dd096461147020079` |
| Foushee projection | `3f793015210c3da9a777f3e0940f82b386aff79ced4ed3715192ad64f02365b6` |
| Massie projection | `ecf22441e891ff3ad05de00fd0ab05f0d1ca1a9692e3a32651d6ea8dbb830714` |

The complete 1,736-character captured bill equals its bound claim passage.
Clerk observations, 405–5 / 20 Not Voting totals, Foushee proposition
`prop:75edca987585935c`, Massie's absent directional proposition, and the singleton
episode were checked. The existing audit remains candidate-quality evidence;
its corrected `AUDIT-SHARED-MEMBER-CHOICES` finding was preserved. No new
independent semantic audit, live-source recapture, or full pipeline replay is
claimed. Recorded raw official-source hashes were not newly verified against
downloaded official bytes.

Local-only proof files, raw file SHA-256. These are not included in this
two-document PR; the pinned Git pointers above provide the reviewable source
binding without depending on local links:

- `.tmp/health-one-action-local-preparation/git-dependency-comparison.json`:
  `f2bb4444bce542a0ad20baee3c59e65f65191fc8b747fd944618b882d0bb6aa6`.
- `.tmp/health-one-action-local-preparation/git-slice-main.json`:
  `7dbe05abe741d3b9cc5f0b39d5315869a3318a4044e738066b428f8a02effb22`.
- `.tmp/health-one-action-local-preparation/git-slice-pr198.json`:
  `f5274cd0e744b4312e29736a7c9ef40425fbc31f940d580504b2abf1751ecbed`.
- `.tmp/health-one-action-local-preparation/git-audit-excerpt.json`:
  `2919ef9a7a17d6f5fb5624d7f0c1c81900c7864a5e897d85a2248864335ac138`.

## Authority that remains absent

The reported editorial decisions do not establish acceptance of a subsequently
extracted/compiled Semantic IR graph, a completed bounded review manifest, a
public-presentation implementation, or a storage payload. Those artifacts do not
yet exist as a validated governed one-action release bundle.

Production eligibility, persistence/import, benchmark promotion, publication of
product/editorial content, registry inclusion, activation, deployment, and merge
remain unauthorized. No database access or production-state inspection occurred.
Existing shared-candidate rejection guards remain intact.

## Separate repository-delivery authorization

The later user response `Authorize`, reference
`Sentinel_2f54bf1741c48191a74ad909bfce22a3`, answers the explicit request at
`Sentinel_e3362bcab64c8191aca0e4301f52fa3a` to commit the receipt and technical
plan to a feature branch and open a draft PR. It resolves the prior automatic
approval rejection for those delivery steps only. The PR contains only these
two documentary files. This authority neither changes the four editorial layers
above nor authorizes the future implementation stages.

The detached input bindings, layer separation, and downstream non-authority
follow the existing [M11D convention](../plans/m11d_national_security_action_meaning_acceptance_v1.md)
and [action-decision governance](../methodology/full_record_action_interpretation_decision_authority_v1.md).
This draft deliberately does not claim the full-record authority schema passed:
its required candidate, readiness, universe, and implementation bindings have
not been produced for this bounded slice. It introduces no replacement schema
or automatic consumer.

Next technical work is described in the [local preparation plan](../plans/health_one_action_local_preparation.md).
