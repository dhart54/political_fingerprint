# Foushee Justice Action-Interpretation Generalization Review

> Candidate, non-authorizing, non-public working material. Nothing in this dossier is accepted or publication-eligible.

## Human decision requested

Choose exactly one after review: `generalization_pass`, `global_revision_required`, or `generalization_rejected`.

## Frozen inputs and method

- Candidate batch: `action-interpretation-candidates:f000477:justice_public_safety:119:v1`
- Frozen subject SHA-256: `78c210d38f67e3ba357af4bd8f077673b05fcfc4a6b61881727789087cd17c00`
- Random seed SHA-256: `bed1535aa44be6c9f8a897684e2290cb1ef5a854f783e853487f4568f6bfda38`
- Random algorithm: sha256_rank_without_replacement_v1: sort by SHA-256(seed_sha256 + LF + action_id), then action_id; take first 12

Random sample: `house:119:1:351`, `house:119:1:68`, `house:119:1:162`, `house:119:2:155`, `house:119:1:270`, `house:119:2:234`, `house:119:2:171`, `house:119:1:340`, `house:119:1:274`, `house:119:2:273`, `house:119:1:42`, `house:119:1:298`

Challenge set:
- `house:119:1:166` — required Senate-origin S. 331 action
- `house:119:2:155` — required FISA roll 155; low confidence; candidate status ambiguous; unresolved generator/reviewer disposition; major adversarial finding
- `house:119:2:157` — highest deterministic source-complexity suspension passage as amended
- `house:119:2:221` — required FISA roll 221
- `house:119:2:273` — highest deterministic source-complexity amendment
- `house:119:2:278` — low confidence; candidate status no_safe_candidate; unresolved generator/reviewer disposition; major adversarial finding

## Benchmark controls

| Action | Relationship | Severity | Explanation |
|---|---|---|---|
| `house:119:1:130` | aligned | none | Both identify the retired-service-weapon purchase program. |
| `house:119:1:131` | aligned | none | Both identify Attorney General reporting on attacks and officer wellness. |
| `house:119:1:166` | aligned | none | Both identify the later fentanyl scheduling framework and research provisions. |
| `house:119:1:275` | acceptably_narrower | minor | The candidate identifies D.C. pursuit standards but does not capture the accepted reference's broader-authority and exceptions detail. |
| `house:119:1:299` | broader_than_reference | major | The candidate follows the official title's repeal description but omits that specified provisions were retained; the accepted reference is materially narrower. |
| `house:119:1:32` | aligned | none | The candidate states the certification trigger in greater exact-action detail. |
| `house:119:1:33` | aligned | none | Both identify passage of the earlier HALT Fentanyl framework. |

## Cases requiring focused attention

- `house:119:2:155` — status `ambiguous`, confidence `low`, review severity `major`.
- `house:119:2:278` — status `no_safe_candidate`, confidence `low`, review severity `major`.

## Sampled and challenged action detail

### house:119:1:162

- Identity/stage: `119:hr:2096` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `medium`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:2096; the operative text states its purpose as: To restore the right to negotiate matters pertaining to the discipline of law enforcement officers of the District of Columbia through collective bargaining, to restore the statute of limitations for bringing disciplinary cases against members or civilian employees of the Metropolitan Police Department of the District of Columbia, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:162:v1` / `ef459b0f1781a22cbe7d31b29180e74e9cb8350f58177509085870938e366eef`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:2096; the operative text states its purpose as: To restore the right to negotiate matters pertaining to the discipline of law enforcement officers of the District of Columbia through collective bargaining, to restore the statute of limitations for bringing disciplinary cases against members or civilian employees of the Metropolitan Police Department of the District of Columbia, and for other purposes. (`congress_text:119:hr:2096:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:166

- Identity/stage: `119:s:331` / `passage`
- Official member action: `yea`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `supports_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:s:331; the operative text states its purpose as: To amend the Controlled Substances Act with respect to the scheduling of fentanyl-related substances, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:166:v1` / `7dff1f8cf3a235c70133923fbdcd29e990da8fff93a9128d435fa3dd06d8db10`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:s:331; the operative text states its purpose as: To amend the Controlled Substances Act with respect to the scheduling of fentanyl-related substances, and for other purposes. (`congress_text:119:s:331:enr`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:270

- Identity/stage: `119:hr:4922` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `medium`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:4922; the operative text states its purpose as: To limit youth offender status in the District of Columbia to individuals 18 years of age or younger, to direct the Attorney General of the District of Columbia to establish and operate a publicly accessible website containing updated statistics on juvenile crime in the District of Columbia, to amend the District of Columbia Home Rule Act to prohibit the Council of the District of Columbia from enacting changes to existing criminal liability sentences, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:270:v1` / `85c2d31548d27da99c4275b65a176be7c183bbe1ee34044c3a059efc9a4d66b5`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:4922; the operative text states its purpose as: To limit youth offender status in the District of Columbia to individuals 18 years of age or younger, to direct the Attorney General of the District of Columbia to establish and operate a publicly accessible website containing updated statistics on juvenile crime in the District of Columbia, to amend the District of Columbia Home Rule Act to prohibit the Council of the District of Columbia from enacting changes to existing criminal liability sentences, and for other purposes. (`congress_text:119:hr:4922:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:274

- Identity/stage: `119:hr:5125` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:5125; the operative text states its purpose as: To amend the District of Columbia Home Rule Act to terminate the District of Columbia Judicial Nomination Commission, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:274:v1` / `db9c00671c7061a36dcf9834bf732fd6562c2a39f35f5e9ecfef855c387e6568`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:5125; the operative text states its purpose as: To amend the District of Columbia Home Rule Act to terminate the District of Columbia Judicial Nomination Commission, and for other purposes. (`congress_text:119:hr:5125:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:298

- Identity/stage: `119:hr:5214` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:5214; the operative text states its purpose as: To require mandatory pretrial and post conviction detention for crimes of violence and dangerous crimes and require mandatory cash bail for certain offenses that pose a threat to public safety or order in the District of Columbia, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:298:v1` / `6eedb7130c49dbc68d121a856b0f9716673ba0b6ff358b39f2420e1f5ae750b6`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:5214; the operative text states its purpose as: To require mandatory pretrial and post conviction detention for crimes of violence and dangerous crimes and require mandatory cash bail for certain offenses that pose a threat to public safety or order in the District of Columbia, and for other purposes. (`congress_text:119:hr:5214:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:340

- Identity/stage: `119:hr:4371` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:4371; the operative text states its purpose as: To amend the William Wilberforce Trafficking Victims Protection Reauthorization Act of 2008 and the Homeland Security Act of 2002 to enhance efforts to combat the trafficking of children.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:340:v1` / `6178de2a614879fc1f1025965c585cf0ce77e466774bb8d5289110e199b29745`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:4371; the operative text states its purpose as: To amend the William Wilberforce Trafficking Victims Protection Reauthorization Act of 2008 and the Homeland Security Act of 2002 to enhance efforts to combat the trafficking of children. (`congress_text:119:hr:4371:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:351

- Identity/stage: `119:hr:3492` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:3492; the operative text states its purpose as: To amend section 116 of title 18, United States Code, with respect to genital and bodily mutilation and chemical castration of minors.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:351:v1` / `ae47318b2228c57071dd085ed75d868f52d9fe9272901a532f9b896fe5e6e0ad`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:3492; the operative text states its purpose as: To amend section 116 of title 18, United States Code, with respect to genital and bodily mutilation and chemical castration of minors. (`congress_text:119:hr:3492:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:42

- Identity/stage: `119:hr:35` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:35; the operative text states its purpose as: To impose criminal and immigration penalties for intentionally fleeing a pursuing Federal officer while operating a motor vehicle.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:42:v1` / `82324b4f9afd44d3c363db1c86890fcdb6d0dbd2afaa59ddf63601a7ecb27d77`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:35; the operative text states its purpose as: To impose criminal and immigration penalties for intentionally fleeing a pursuing Federal officer while operating a motor vehicle. (`congress_text:119:hr:35:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:1:68

- Identity/stage: `119:hr:1156` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:1156; the operative text states its purpose as: To amend the CARES Act to extend the statute of limitations for fraud under certain unemployment programs, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:1:68:v1` / `279995ce87c859821d4bfa4f71d7e0491e647f0eb394dfd38870b4f26c765396`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:1156; the operative text states its purpose as: To amend the CARES Act to extend the statute of limitations for fraud under certain unemployment programs, and for other purposes. (`govinfo_text_119_hr1156_eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:155

- Identity/stage: `119:s:4465` / `suspension_passage`
- Official member action: `nay`
- Candidate status/confidence: `ambiguous` / `low`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the suspension_passage stage was whether to pass 119:s:4465; the operative text states its purpose as: To amend the FISA Amendments Act of 2008 to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:155:v1` / `cdd2269c543f4f496a2fc71a638a25020dd5065ecf064bed9253f04f752bc05d`
- Claim components:
  - The House choice at the suspension_passage stage was whether to pass 119:s:4465; the operative text states its purpose as: To amend the FISA Amendments Act of 2008 to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978, and for other purposes. (`govinfo_text_119_s4465_es`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: The supplied text may be the intended Title VII extension language despite its document-title metadata.
- Limitations: Governed operative XML title metadata conflicts with the packet's Congress/measure identity.
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: surveillance_authority; fisc_and_court_authority; civil_liberty_protections
- Adversarial recommendation/severity: `candidate_ambiguous` / `major`
- Findings:
  - `house:119:2:155:finding:1`: The governed XML document title identifies 110 S4465 while the neutral packet identifies 119:s:4465. Recommended correction: Preserve the bounded FISA extension description as ambiguous and low confidence; do not broaden it.
- Review questions: Can a later human review reconcile the official raw-text metadata with the governed action identity?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:157

- Identity/stage: `119:hr:2853` / `suspension_passage_as_amended`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the suspension_passage_as_amended stage was whether to pass 119:hr:2853; the operative text states its purpose as: To combat organized crime involving the illegal acquisition of retail goods and cargo for the purpose of selling those illegally obtained goods through physical and online retail marketplaces.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:157:v1` / `26067933d9c1df456f3fca89d36be4480eb3f9553dc7c8269025c54267fa3301`
- Claim components:
  - The House choice at the suspension_passage_as_amended stage was whether to pass 119:hr:2853; the operative text states its purpose as: To combat organized crime involving the illegal acquisition of retail goods and cargo for the purpose of selling those illegally obtained goods through physical and online retail marketplaces. (`govinfo_text_119_hr2853_eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:171

- Identity/stage: `119:hr:5625` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the passage stage was whether to pass 119:hr:5625; the operative text states its purpose as: To direct the Attorney General to make publicly available a list of each State and unit of local government that permits cashless bail, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:171:v1` / `23cfc0f83b8eacad74245d24235b9098530ae98eda3c3ca55fe66201229baa2f`
- Claim components:
  - The House choice at the passage stage was whether to pass 119:hr:5625; the operative text states its purpose as: To direct the Attorney General to make publicly available a list of each State and unit of local government that permits cashless bail, and for other purposes. (`govinfo_text_119_hr5625_eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:221

- Identity/stage: `119:hr:9238` / `suspension_passage`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice at the suspension_passage stage was whether to pass 119:hr:9238; the operative text states its purpose as: To amend the FISA Amendments Act of 2008 to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:221:v1` / `603d1b9c62e2f4ff3e625796716c8f0c0739791ac257923679dce227c213e506`
- Claim components:
  - The House choice at the suspension_passage stage was whether to pass 119:hr:9238; the operative text states its purpose as: To amend the FISA Amendments Act of 2008 to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978, and for other purposes. (`govinfo_text_119_hr9238_cdh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: surveillance_authority; fisc_and_court_authority; civil_liberty_protections
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:234

- Identity/stage: `119:hr:3106` / `suspension_passage`
- Official member action: `yea`
- Candidate status/confidence: `proposed` / `high`
- Exact-choice position effect: `supports_exact_choice`
- Candidate meaning: The House choice at the suspension_passage stage was whether to pass 119:hr:3106; the operative text states its purpose as: To require the Secretary of Homeland Security to conduct a collective response to a terrorism exercise that includes the management of cascading effects on critical infrastructure during times of extreme cold weather, and for other purposes.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:234:v1` / `c354c798478c4114b2c37c3daf205376b9018f959e5dba0bffc9b0a57671d6ae`
- Claim components:
  - The House choice at the suspension_passage stage was whether to pass 119:hr:3106; the operative text states its purpose as: To require the Secretary of Homeland Security to conduct a collective response to a terrorism exercise that includes the management of cascading effects on critical infrastructure during times of extreme cold weather, and for other purposes. (`congress_text:119:hr:3106:eh`, official-title, `directly_supported`; limitation: none)
- Competing plausible interpretations: none recorded
- Limitations: none recorded
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:273

- Identity/stage: `house:119:2:273` / `amendment`
- Official member action: `nay`
- Candidate status/confidence: `proposed` / `medium`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: The House choice was whether to codify duties, responsibilities, and protections for military chaplains, including religious-exercise and confidentiality protections, and make specified violations subject to the Uniform Code of Military Justice.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:273:v1` / `f766d7678c283ee776018bc6d4549df6a52254b68f66ddbe8b194b0b87df7fb0`
- Claim components:
  - The House choice was whether to codify duties, responsibilities, and protections for military chaplains, including religious-exercise and confidentiality protections, and make specified violations subject to the Uniform Code of Military Justice. (`rules-report-2026-07-20-amendment-28`, governed PDF pages 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, `supported_with_limitation`; limitation: Deterministic page-bound extraction preserves the governed PDF and page locators; line geometry and typography are not preserved.)
- Competing plausible interpretations: none recorded
- Limitations: Deterministic page-bound extraction preserves the governed PDF and page locators; line geometry and typography are not preserved.
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `retain_candidate` / `none`
- Findings:
  - No finding.
- Review questions: Does the exact wording remain bounded to the supplied evidence?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

### house:119:2:278

- Identity/stage: `119:hr:8800` / `passage`
- Official member action: `nay`
- Candidate status/confidence: `no_safe_candidate` / `low`
- Exact-choice position effect: `opposes_exact_choice`
- Candidate meaning: No safe substantive candidate.
- Evidence-map: `action-interpretation-evidence-map:house:119:2:278:v1` / `95f6cace81ce178e57bdfdedfdea07e76efccf57fddad248ce3200232f5f2659`
- Claim components:
  - None; the final status is `no_safe_candidate`.
- Competing plausible interpretations: The choice can be described only as passage of the FY2027 NDAA as amended; its complete substantive scope is not safely recoverable from this packet.
- Limitations: Deterministic page-bound extraction preserves the governed PDF and page locators; line geometry and typography are not preserved.; The packet does not isolate the complete final House-passed operative package.
- Does not establish: motive; ideology; party loyalty; a general issue position; support or opposition beyond the exact House choice; a policy trajectory; an episode-level position; a repeated pattern
- Cross-domain limitations: none
- Adversarial recommendation/severity: `no_safe_candidate` / `major`
- Findings:
  - `house:119:2:278:finding:1`: The governed Rules report identifies the initial substitute, amendment process, and an engrossment addition, but does not itself reproduce the complete final House-passed text after floor amendments. Recommended correction: Use no_safe_candidate for a substantive final-package interpretation while retaining stage and identity facts.
- Review questions: Is a complete governed final House-passed text required before a substantive candidate can be proposed?
- Structured decision options: `accept_candidate_for_later_full_review`, `accept_with_required_revision`, `reject_candidate`, `unresolved`

## Bounded corrections

Two candidates were revised; all changes are preserved in canonical JSON.

## Likely failure modes

- Official-title wording can omit operative exceptions or retained provisions.
- A governed source can still contain internal identity metadata that requires human reconciliation.
- A Rules report can establish floor structure without isolating the complete final passed text.
- A narrow exact-action candidate must not be expanded into a general issue, motive, ideology, episode, or pattern claim.

## Full 37-action summary matrix

| Action | Stage | Member action | Status | Confidence | Effect | Review | Recommendation |
|---|---|---|---|---|---|---|---|
| `house:119:1:6` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:23` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:27` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:32` | amendment | yea | proposed | medium | supports_exact_choice | none | retain_candidate |
| `house:119:1:33` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:42` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:68` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:98` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:128` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:130` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:131` | passage | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:1:162` | passage | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:1:166` | passage | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:1:270` | passage | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:1:271` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:274` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:275` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:286` | suspension_passage_as_amended | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:1:289` | suspension_passage | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:1:298` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:299` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:340` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:1:351` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:155` | suspension_passage | nay | ambiguous | low | opposes_exact_choice | major | candidate_ambiguous |
| `house:119:2:157` | suspension_passage_as_amended | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:169` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:171` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:218` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:221` | suspension_passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:227` | suspension_passage_as_amended | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:2:234` | suspension_passage | yea | proposed | high | supports_exact_choice | none | retain_candidate |
| `house:119:2:240` | passage | nay | proposed | high | opposes_exact_choice | none | retain_candidate |
| `house:119:2:259` | amendment | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:2:265` | amendment | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:2:273` | amendment | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:2:275` | amendment | nay | proposed | medium | opposes_exact_choice | none | retain_candidate |
| `house:119:2:278` | passage | nay | no_safe_candidate | low | opposes_exact_choice | major | no_safe_candidate |

## Canonical artifact paths and hashes

- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/evidence_maps.json` — `281d2cde6af8dcdea670cf6308edb9268eb361a921bef4b3e75fac63b52c099f`
- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/candidate_batch.json` — `e40a06a443e99216e6e912dfed080f392d00f39811d16aef984284014a6e4e4f`
- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/adversarial_reviews.json` — `3e2a7b593432a9ebe13d2de68fabed2daa02b8a53030fb4c6b8a13ff9c37a6e7`
- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/benchmark_comparison.json` — `e246853345aa4d145bc76cffd4c3003d2ffb7c2e1a159a2266d338f01da95dcc`
- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/sample_manifest.json` — `31b5dabe82b330446dc6fd43c914932f559552e2d14113e3f0f7cd231cb4bd8a`
- `docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v1/human_decision_template.json` — `0ba231faad32a3a6fc7830c953acead8e008bf263b07910dbee522eb6b4c1737`

## Mandatory stop

This bundle requests human generalization review only. It creates no accepted interpretation or downstream semantic authority.
