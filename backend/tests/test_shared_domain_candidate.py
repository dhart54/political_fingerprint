"""Real Health source bindings and focused candidate/update invariants."""
import copy
import json
import unittest
from pathlib import Path

from scripts.prepare_shared_domain_candidate import prepare, readable_candidates, reproducibility_proof, review_text, validate_universe_proposal
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, candidate_update_impact, choice_effect, digest,
    sealed_digest, validate_member_projection, validate_shared_action_core,
    SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.semantic_ir.compiler import SemanticCompilerInputError
from backend.app.semantic_ir.adapters import build_persistence_proposal
from backend.app.editorial_presentations.compiler import compile_public_issue_presentation, EditorialPresentationError

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/editorial/shared_candidates/house_119_health_20260916"


class SharedDomainCandidateTests(unittest.TestCase):
    def test_va_passage_preserves_current_care_boundaries_and_separate_failed_transfer(self):
        aid = 'house:119:2:175'
        action = next(a for a in self.author['actions'] if a['action_id'] == aid)
        for phrase in ['$100million plus a$500,000', 'October1,2027', 'rescinding$1.65billion',
                       'not add these allocations again', 'netting to zero', 'eligible unmarried veterans',
                       'DIVISION D with a2026 deadline', 'not an absolute permanent prohibition',
                       'no automatic FY2027 program extension', 'not federal legalization']:
            self.assertIn(phrase, action['meaning'])
        records = {r['action_id']: r for r in json.loads((DATA / 'membership_review.json').read_text(encoding='utf-8'))['records']}
        self.assertEqual(records['house:119:2:174']['disposition'], 'exact_action_ineligible')
        self.assertIn('not49 PortCharlotte', records['house:119:2:174']['rationale'])
        readable = readable_candidates(self.author, self.products[0], self.products[2], self.products[4])
        for member in readable['members']:
            finding = next(f for f in member['findings'] if aid in f['action_ids'])
            self.assertEqual(finding['action_ids'], [aid])
            self.assertEqual(finding['action_observations'][0]['status'], 'Yea')
            self.assertIn('rescinding specified earlier medical-account balances', finding['compact'])
            self.assertFalse(any('house:119:2:174' in f['action_ids'] for f in member['findings']))

    def test_va_passage_cannot_lose_current_ivf_baseline_or_material_coverage_rule(self):
        for sid in ['govinfo:fr2024-07040-ivf', 'govinfo:38cfr17-4040-2025-specialty', 'govinfo:pl119-37']:
            with self.subTest(source=sid):
                capture = copy.deepcopy(self.capture)
                capture['sources'] = [s for s in capture['sources'] if s['source_id'] != sid]
                with self.assertRaises(KeyError) as caught:
                    prepare(self.author, capture, ['F000477', 'M001184'])
                self.assertEqual(caught.exception.args, (sid,))

    def test_may_controls_do_not_add_health_findings_or_rewrite_farm_passage(self):
        records = {r['action_id']: r for r in json.loads((DATA / 'membership_review.json').read_text(encoding='utf-8'))['records']}
        for disposition, rolls in [('procedural_context', [158,159,160,161,163,168,172]),
                                   ('expressive_nonbinding_context', [162,165,166,167]),
                                   ('exact_action_ineligible', [155,156,157,164,169,170,171,173])]:
            for roll in rolls:
                self.assertEqual(records[f'house:119:2:{roll}']['disposition'], disposition)
        for projection in self.products[2]:
            self.assertFalse({f'house:119:2:{n}' for n in range(155,174)} & {a['action_id'] for a in projection['actions']})
        self.assertIn('retroactively reinterpreting', records['house:119:2:161']['rationale'])
        self.assertIn('Medicines,personal protective equipment and infant-formula scarcity', records['house:119:2:157']['rationale'])
        self.assertIn('medical-care request is real', records['house:119:2:167']['rationale'])
        self.assertIn('rather than prohibiting cashless bail', records['house:119:2:171']['rationale'])

    def test_may_exact_sources_preserve_nondirectional_vote_and_failed_war_timing(self):
        sources = {s['source_id']: s for s in self.capture['sources']}
        records = {r['action_id']: r for r in json.loads((DATA / 'membership_review.json').read_text(encoding='utf-8'))['records']}
        self.assertEqual(sources['clerk:119:2:169']['member_records']['M001184']['official_label'], 'Not Voting')
        self.assertIn('resolved nondirectional', records['house:119:2:169']['rationale'])
        self.assertIn('30days after the specified February28 date', records['house:119:2:170']['rationale'])
        self.assertIn('conditional coalition sharing', records['house:119:2:170']['rationale'])
        self.assertIn('FAILED212-212', records['house:119:2:170']['rationale'])
        self.assertIn('February 28, 2026', sources['congressional-record:2026-05-13-hconres75-exact']['text'])
        self.assertEqual(sources['clerk:119:2:170']['metadata']['vote-result'], 'Failed')
        self.assertIn('June 12, 2026', sources['govinfo:s4465es']['text'])
        self.assertIn('monetary bail', sources['govinfo:hr6260eh']['text'])

    def test_farm_amendments_retain_separate_snap_choices_and_failed_restriction(self):
        actions = {a['action_id']: a for a in self.author['actions']}
        ids = [f'house:119:2:{n}' for n in [145, 146, 151]]
        for aid in ids:
            self.assertEqual(actions[aid]['stage'], 'amendment')
            self.assertEqual(actions[aid]['episode_id'], 'episode:hr7567:119')
        self.assertIn('other existing meal exceptions', actions[ids[0]]['compact_description'])
        self.assertIn('after all such projects conclude', actions[ids[1]]['compact_description'])
        self.assertIn('would not itself prohibit foods', actions[ids[1]]['compact_description'])
        self.assertIn('artificial sweetener or flavoring per serving', actions[ids[2]]['compact_description'])
        self.assertIn('amendment failed', actions[ids[2]]['compact_description'])
        readable = readable_candidates(self.author, self.products[0], self.products[2], self.products[4])
        for member in readable['members']:
            finding = next(f for f in member['findings'] if ids[0] in f['action_ids'])
            self.assertEqual(finding['action_ids'], ids + ['house:119:2:154'])
            self.assertIn('neither creates demonstration authority nor adopts any particular food restriction', ' '.join(finding['detail']))
            self.assertIn('failed separate restriction choice, not an adopted component', ' '.join(finding['detail']))
        for projection in self.products[2]:
            rows = {r['action_id']: r for r in projection['actions']}
            self.assertEqual(rows[ids[0]]['official_status'], 'Yea')
            self.assertEqual(rows[ids[1]]['official_status'], 'Yea')
            self.assertEqual(rows[ids[2]]['official_status'], 'Nay' if projection['member_id'] == 'F000477' else 'Yea')
        author = copy.deepcopy(self.author)
        next(a for a in author['actions'] if a['action_id'] == ids[0])['additional_source_ids'].remove('govinfo:7usc2012-2024-snap-definitions')
        with self.assertRaisesRegex(ValueError, 'compact meaning|claim passage absent'):
            prepare(author, self.capture, ['F000477', 'M001184'])

    def test_april_farm_controls_bind_house_versions_and_modified_exact_amendment(self):
        records = {r['action_id']: r for r in json.loads((DATA / 'membership_review.json').read_text(encoding='utf-8'))['records']}
        sources = {s['source_id']: s for s in self.capture['sources']}
        for n in [140, 141, 143, 153]:
            self.assertEqual(records[f'house:119:2:{n}']['disposition'], 'procedural_context')
        for n in [142, 144, 147, 148, 149, 150, 152]:
            self.assertEqual(records[f'house:119:2:{n}']['disposition'], 'exact_action_ineligible')
        self.assertIn('not cemetery-marker ES', records['house:119:2:142']['rationale'])
        self.assertTrue(any(s['source_id'] == 'govinfo:s1318eah' for s in records['house:119:2:142']['sources']))
        self.assertIn('not appropriations', records['house:119:2:143']['rationale'])
        self.assertIn('replacing everyPage430 reference byPage431', records['house:119:2:150']['rationale'])
        self.assertIn('NOT Scholten PartB45', records['house:119:2:150']['rationale'])
        self.assertIn('Page 431', sources['congressional-record:2026-04-29-farm-exact-amendments']['text'])
        self.assertIn('paragraphs (1) through (5)', sources['rules:hr7567-print119-22-material-amendment-pages']['text'])
        excluded = {f'house:119:2:{n}' for n in [140,141,142,143,144,147,148,149,150,152,153]}
        for projection in self.products[2]:
            self.assertFalse(excluded & {r['action_id'] for r in projection['actions']})

    def test_late_april_reporting_and_environment_reviews_retain_material_context_without_direction(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for n in [125, 126, 127, 129, 134, 136, 137, 138]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "exact_action_ineligible")
        self.assertEqual(records["house:119:2:132"]["disposition"], "expressive_nonbinding_context")
        for n in [130, 131, 133, 135]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "procedural_context")
        for n, phrase in [(126, "Dispatching appropriate emergency response providers"),
                          (127, "without an improvement to the hardware or software"),
                          (134, "radon and other indoor air pollutants"),
                          (136, "protection of public health is the highest priority"),
                          (137, "shall not apply to actions on Indian lands")]:
            self.assertTrue(any(phrase in b["passage"] for b in records[f"house:119:2:{n}"]["claim_source_map"]))
        self.assertIn("Medicaid/CHIP", records["house:119:2:132"]["rationale"])
        self.assertIn("Not Voting is nondirectional", records["house:119:2:132"]["rationale"])
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in [125,126,127,129,130,131,132,133,134,135,136,137,138]} & {a["action_id"] for a in projection["actions"]})

    def test_april_midmonth_controls_preserve_exact_failed_amendment_and_adjacent_health_context(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for n in [109, 110, 114, 116, 118, 120]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "exact_action_ineligible")
        for n in [111, 112, 113, 115, 117, 119, 122, 123, 124]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "procedural_context")
        self.assertEqual(records["house:119:2:121"]["disposition"], "expressive_nonbinding_context")
        for phrase in ["air-ambulance/air-medical", "drug/alcohol", "occupational"]:
            self.assertIn(phrase.lower(), records["house:119:2:110"]["rationale"].lower())
        self.assertIn("State/local public assistance", records["house:119:2:120"]["rationale"])
        self.assertIn("outside the NONATTAINMENT AREA", records["house:119:2:116"]["rationale"])
        self.assertIn("retaining proposed-legislation review", records["house:119:2:118"]["rationale"])
        floor = sources["congressional-record:2026-04-16-hres1175"]["text"]
        self.assertIn("Print 119–25 shall be considered as adopted.", floor)
        self.assertIn("So the amendment was rejected.", floor)
        self.assertIn("So the resolution was not agreed to.", floor)
        self.assertEqual(sources["clerk:119:2:123"]["member_records"]["M001184"]["official_label"], "Nay")
        for n in [111, 112, 121]:
            old, new = sources[f"clerk:119:2:{n}"], sources[f"clerk:119:2:{n}:continuation-recapture"]
            for field in ["metadata", "member_records", "party_totals"]:
                self.assertEqual(old[field], new[field])
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in range(109, 125)} & {a["action_id"] for a in projection["actions"]})

    @classmethod
    def setUpClass(cls):
        cls.author = json.loads((DATA / "authoring.json").read_text(encoding="utf-8"))
        cls.capture = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
        cls.products = prepare(cls.author, cls.capture, ["F000477", "M001184"])

    def test_remote_access_and_trade_preferences_keep_health_counterevidence_without_findings(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        authored = {a["action_id"] for a in self.products[0]["actions"]}
        for roll in [13, 14, 15]:
            aid = f"house:119:2:{roll}"
            self.assertEqual(records[aid]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[aid]["substantive_review_performed"])
            self.assertNotIn(aid, authored)
        self.assertIn("humanitarian donations", records["house:119:2:13"]["rationale"])
        self.assertIn("health-care availability", records["house:119:2:14"]["rationale"])
        self.assertIn("TAICNAR", records["house:119:2:15"]["rationale"])
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("September 30, 2031", sources["olrc:19usc3805-2024-korea503"]["text"])
        self.assertIn("after September 30, 2025", sources["govinfo:hr6500eh"]["text"])
        self.assertIn("on or after September 30, 2025", sources["govinfo:hr6504eh"]["text"])
        self.assertIn("occupational health and safety", sources["olrc:19usc2703a-2024-operative"]["text"])

    def test_offline_determinism_and_checked_in_outputs(self):
        core, mapping, projections, inputs, result = self.products
        again = prepare(self.author, self.capture, ["F000477", "M001184"])
        self.assertEqual(digest(result.compiled_ir), digest(again[-1].compiled_ir))
        outputs = {"shared_action_core": core, "shared_issue_mapping": mapping,
            "member_projections": projections, "compiler_input": inputs, "compiled_ir": result.compiled_ir,
            "readable_candidates": readable_candidates(self.author, core, projections, result)}
        for name, value in outputs.items():
            self.assertEqual(value, json.loads((DATA / "generated" / f"{name}.json").read_text(encoding="utf-8")), name)

    def test_dc_tax_disapproval_binds_target_credit_limits_and_later_outcome(self):
        action = next(a for a in self.author["actions"] if a["action_id"] == "house:119:2:56")
        self.assertEqual((action["bill_type"], action["episode_id"]), ("hjres", "episode:hjres142:119"))
        self.assertEqual(action["source_id"], "govinfo:hjres142eh")
        for term in ["whole package", "public-assistance eligibility", "24.25 percent",
                     "District tax otherwise due", "leaving 2025 outside", "December 31, 2025",
                     "would not materially affect", "later February 24", "not the named target"]:
            self.assertIn(term, action["meaning"])
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("32%", sources["dc-council:47-1806.04-permanent-care-earned"]["text"])
        self.assertIn("85%", sources["dc-council:47-1806.04-permanent-care-earned"]["text"])
        self.assertIn("before January 1, 2025", sources["dc-council:act26-217-operative"]["text"])
        self.assertIn("after December 31, 2025", sources["govinfo:pl119-21-standard-senior-care"]["text"])
        self.assertIn("Section 47-1806.17", sources["dc-council:dc26-55-child-credit-repeal"]["text"])
        f, m = [{a["action_id"]: a for a in p["actions"]} for p in self.products[2]]
        self.assertEqual((f[action["action_id"]]["official_status"], m[action["action_id"]]["official_status"]), ("Nay", "Yea"))
        self.assertEqual(f[action["action_id"]]["action_core_sha256"], m[action["action_id"]]["action_core_sha256"])

    def test_joint_resolution_measure_binding_rejects_bill_and_unknown_type(self):
        for kind in ["hr", "unrecognized"]:
            changed = copy.deepcopy(self.author)
            action = next(a for a in changed["actions"] if a["action_id"] == "house:119:2:56")
            action["bill_type"] = kind
            with self.assertRaisesRegex(ValueError, "Clerk measure and proposed text differ"):
                prepare(changed, self.capture, ["F000477", "M001184"])

    def test_real_members_reuse_meaning_for_matching_different_and_nonvoting_choices(self):
        core, _, projections, _, _ = self.products
        f, m = [{a["action_id"]: a for a in p["actions"]} for p in projections]
        self.assertEqual(f["house:119:1:349"]["official_status"], m["house:119:1:349"]["official_status"])
        self.assertEqual((f["house:119:1:362"]["official_status"], m["house:119:1:362"]["official_status"]), ("Nay", "Yea"))
        self.assertEqual(m["house:119:1:306"]["official_status"], "Not Voting")
        for action in core["actions"]:
            aid = action["action_id"]
            self.assertEqual(f[aid]["action_core_sha256"], m[aid]["action_core_sha256"])
            for row in [f[aid], m[aid]]:
                self.assertEqual(row["exact_choice_effect"], choice_effect(row["official_status"]))

    def test_proof_and_readable_packet_are_reproducible(self):
        proof = reproducibility_proof(self.author, self.capture, ["F000477", "M001184"])
        self.assertEqual(proof, json.loads((DATA / "generated/reproducibility_proof.json").read_text(encoding="utf-8")))
        core, _, projections, _, result = self.products
        packet = (ROOT / "docs/review_packets/foushee_health_shared_candidate.md").read_text(encoding="utf-8")
        generated = packet.split("<!-- GENERATED CANDIDATE START -->\n", 1)[1].split("<!-- GENERATED CANDIDATE END -->", 1)[0]
        self.assertEqual(generated, review_text(self.author, core, projections, result, self.capture))
        other = prepare(self.author, self.capture, ["M001184"])
        self.assertTrue(review_text(self.author, other[0], other[2], other[-1], self.capture).startswith("## Generated Massie candidate findings"))

    def test_member_identity_and_party_do_not_change_graph(self):
        inputs = copy.deepcopy(self.products[3])
        expected = self.products[-1].compiled_ir["members"][0]
        inputs["members"] = [inputs["members"][0]]
        inputs["members"][0].update(member_id="synthetic-identity", party="synthetic-party")
        result = run_editorial_pipeline(inputs).compiled_ir["members"][0]
        for field in ["coverage", "proposition_graph", "composition", "action_accounting"]:
            self.assertEqual(expected[field], result[field])

    def test_projection_cannot_override_meaning(self):
        core, _, projections, _, _ = self.products
        p = copy.deepcopy(projections[0])
        p["actions"][0]["candidate_exact_action_meaning"] = "different"
        p["projection_sha256"] = sealed_digest(p, "projection_sha256")
        with self.assertRaises(SharedCorpusValidationError):
            validate_member_projection(ROOT, p, core)

    def test_proposed_state_cannot_be_laundered_as_accepted(self):
        core = copy.deepcopy(self.products[0])
        core["authoritative_for_new_editorial_work"] = True
        core.pop("review_state")
        with self.assertRaisesRegex(SharedCorpusValidationError, "authority disagree"):
            validate_shared_action_core(ROOT, core)
        inputs = copy.deepcopy(self.products[3]); inputs.pop("review_state")
        with self.assertRaisesRegex(SemanticCompilerInputError, "explicit candidate"):
            run_editorial_pipeline(inputs)

    def test_candidates_cannot_prepare_public_or_persistence_artifacts(self):
        inputs = self.products[3]; compiled = self.products[-1].compiled_ir
        with self.assertRaisesRegex(ValueError, "cannot prepare"):
            run_editorial_pipeline(inputs, prepare_persistence_proposal=True)
        with self.assertRaises(ValueError):
            build_persistence_proposal(compiled)
        with self.assertRaises(EditorialPresentationError):
            compile_public_issue_presentation(compiled, {}, trusted_action_source_contract={})

    def test_source_and_claim_mutations_fail(self):
        capture = copy.deepcopy(self.capture); capture["sources"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "governed source changed"):
            prepare(self.author, capture, ["F000477"])
        author = copy.deepcopy(self.author); author["actions"][2]["claim_source_map"][0]["passage"] = "invented passage"
        with self.assertRaisesRegex(ValueError, "claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_exact_action_cutoff_and_member_guards(self):
        author = copy.deepcopy(self.author); author["interpretation_action_set_cutoff"] = "2026-07-22"
        with self.assertRaisesRegex(ValueError, "cannot extend"):
            prepare(author, self.capture, ["F000477"])
        with self.assertRaisesRegex(ValueError, "does not contain member"):
            prepare(self.author, self.capture, ["synthetic-absent"])

    def test_division_retention_keeps_exact_scope_and_member_choices(self):
        core, mapping, projections, _, result = self.products
        aid = "house:119:2:5"
        action = next(a for a in core["actions"] if a["action_id"] == aid)
        self.assertEqual(action["legislative_stage"], "division_retention")
        self.assertEqual(action["exact_question"], "On Retaining Division A")
        boundary = action["package_component_boundary"]
        self.assertEqual(boundary["boundary_type"], "specified_divisions")
        self.assertFalse(boundary["parent_package_meaning_projected"])
        self.assertEqual(boundary["governed_component_relationships"],
                         ["Retaining Division A; distinct from whole-bill passage"])
        choices = [next(a for a in p["actions"] if a["action_id"] == aid) for p in projections]
        self.assertEqual([a["official_status"] for a in choices], ["Yea", "Nay"])
        self.assertEqual(choices[0]["action_core_sha256"], choices[1]["action_core_sha256"])
        source_ids = {s["source_id"] for s in action["operative_meaning_source_identities"]}
        self.assertTrue({"govinfo:hr6938ih-division-a", "govinfo:hr6938eh-division-a",
                         "govinfo:hres977eh", "congressional-record:2026-01-08-6938-retention"} <= source_ids)
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for version in ["ih", "eh"]:
            text = sources[f"govinfo:hr6938{version}-division-a"]["text"]
            self.assertIn("$403,000,000", text)
            self.assertIn("Sec. 544.", text)
            self.assertNotIn("DIVISION B--ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES APPROPRIATIONS ACT, 2026 TITLE I CORPS", text)
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid, "house:119:2:6", "house:119:2:7"])

    def test_three_6938_choices_preserve_division_and_passage_boundaries(self):
        core, _, projections, _, result = self.products
        actions = {a["action_id"]: a for a in core["actions"]}
        six = actions["house:119:2:6"]
        seven = actions["house:119:2:7"]
        self.assertEqual(six["exact_question"], "On Retaining Divisions B and C")
        self.assertEqual(six["legislative_stage"], "division_retention")
        self.assertEqual(six["package_component_boundary"]["governed_component_relationships"],
                         ["Retaining Divisions B and C; distinct from whole-bill passage"])
        self.assertEqual(seven["legislative_stage"], "final_passage")
        b_sources = {s["source_id"] for s in six["operative_meaning_source_identities"]}
        passage_sources = {s["source_id"] for s in seven["operative_meaning_source_identities"]}
        self.assertNotIn("govinfo:hr6938ih-division-a", b_sources)
        self.assertTrue({"govinfo:hr6938ih-division-a", "govinfo:hr6938eh-divisions-b-c",
                         "congressional-record:2026-01-08-6938-passage-result"} <= passage_sources)
        for member, expected in zip(projections, ["Yea", "Nay"]):
            rows = {a["action_id"]: a for a in member["actions"]}
            self.assertEqual([rows[f"house:119:2:{n}"]["official_status"] for n in [5, 6, 7]],
                             [expected] * 3)
        authored = {a["action_id"]: a for a in self.author["actions"]}
        for n in [6, 7]:
            meaning = authored[f"house:119:2:{n}"]["meaning"]
            self.assertIn("$4.722738 billion in earlier advances", meaning)
            self.assertIn("rather than legal caps", meaning)
            self.assertIn("pre-May1,2006", meaning)
            self.assertIn("$95.419 million", meaning)
        self.assertIn("abortion-funding restriction", authored["house:119:2:7"]["meaning"])

    def test_division_retention_rejects_wrong_portion_or_passage_stage(self):
        for portion in [None, "Divisions B and C", "Division A and B", ["A"]]:
            author = copy.deepcopy(self.author)
            action = next(a for a in author["actions"] if a["action_id"] == "house:119:2:5")
            action["retained_portion"] = portion
            with self.subTest(portion=portion), self.assertRaisesRegex(ValueError, "candidate stage differs"):
                prepare(author, self.capture, ["F000477"])
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:2:5")
        action["stage"] = "final_passage"
        with self.assertRaisesRegex(ValueError, "retained portion requires"):
            prepare(author, self.capture, ["F000477"])
        action.pop("retained_portion")
        with self.assertRaisesRegex(ValueError, "candidate stage differs"):
            prepare(author, self.capture, ["F000477"])

    def test_retention_cannot_drop_final_report_override_source(self):
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:2:5")
        action["additional_source_ids"].remove("congressional-record:2026-01-08-6938-explanation-a")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_veto_override_keeps_failed_result_and_explicit_eligibility_basis(self):
        core, _, projections, _, _ = self.products
        action = next(a for a in core["actions"] if a["action_id"] == "house:119:2:8")
        self.assertEqual(action["legislative_stage"], "veto_override")
        self.assertEqual(action["exact_question"],
                         "Passage, Objections of the President To The Contrary Notwithstanding")
        self.assertEqual(action["chamber_outcome"], "Failed")
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("the eligibility of the Tribe and its members for any Federal health",
                      sources["govinfo:pl105-313"]["text"])
        self.assertEqual(sources["govinfo:hr504enr"]["text_version"], "ENR")
        self.assertEqual(sources["govinfo:pl105-313"]["source_type"], "official_statutory_text")
        for projection in projections:
            row = next(a for a in projection["actions"] if a["action_id"] == "house:119:2:8")
            self.assertEqual(row["official_status"], "Yea")
        self.assertNotIn("house:119:2:9", {a["action_id"] for a in core["actions"]})
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:2:8")["stage"] = "final_passage"
        with self.assertRaisesRegex(ValueError, "candidate stage differs"):
            prepare(author, self.capture, ["F000477"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:1:33")["stage"] = "veto_override"
        with self.assertRaisesRegex(ValueError, "candidate stage differs"):
            prepare(author, self.capture, ["F000477"])

    def test_raw_ledger_update_does_not_extend_interpretation(self):
        capture = copy.deepcopy(self.capture)
        source = {"source_id": "synthetic:raw-later", "text": "new uninterpreted ledger observation"}
        source["governed_bytes_sha256"] = digest(source); capture["sources"].append(source)
        result = prepare(self.author, capture, ["F000477", "M001184"])
        self.assertEqual(digest(self.products[-1].compiled_ir), digest(result[-1].compiled_ir))
        self.assertEqual(self.products[0], result[0])

    def test_shared_correction_identifies_both_members_and_findings(self):
        core, _, projections, _, result = self.products
        changed = copy.deepcopy(core)
        action = next(a for a in changed["actions"] if a["action_id"] == "house:119:1:362")
        action["candidate_shared_limitations"].append("Synthetic controlled correction; not accepted or published.")
        action["action_core_sha256"] = sealed_digest(action, "action_core_sha256")
        changed["corpus_sha256"] = digest(changed["actions"])
        impact = candidate_update_impact(core, changed, projections, result.compiled_ir)
        self.assertEqual(impact["changed_action_ids"], ["house:119:1:362"])
        self.assertEqual({x["member_id"] for x in impact["affected_projections"]}, {"F000477", "M001184"})
        self.assertEqual(len(impact["affected_findings"]), 2)
        with self.assertRaisesRegex(SharedCorpusValidationError, "wrong action digest"):
            validate_member_projection(ROOT, projections[0], changed)
        self.assertNotEqual(core["corpus_sha256"], changed["corpus_sha256"])

    def test_complete_supplied_accounting_and_real_paired_episode(self):
        core, mapping, projections, _, result = self.products
        all_ids = {a["action_id"] for a in core["actions"]}
        for member in result.compiled_ir["members"]:
            acc = member["action_accounting"]
            represented = set(acc["behavioral_proposition_action_ids"])
            reasons = {r["action_id"] for r in acc["non_proposition_reasons"]}
            self.assertFalse(represented & reasons)
            self.assertEqual(represented | reasons, all_ids)
        pair = next(e for e in mapping["episodes"] if len(e["action_ids"]) == 2)
        self.assertEqual(pair["action_ids"], ["house:119:1:150", "house:119:1:151"])
        for member, status, direction in zip(result.compiled_ir["members"], ["Yea", "Nay"], ["support", "opposition"]):
            p = next(p for p in member["proposition_graph"]["propositions"] if any(o["action_id"] == "house:119:1:150" for o in p.get("action_observations", [])))
            self.assertEqual(p["proposition_type"], "notable_choice")
            self.assertEqual(p["direction"], direction)
            self.assertEqual([o["action_id"] for o in p["action_observations"]], pair["action_ids"])
            self.assertEqual([o["status"] for o in p["action_observations"]], [status, status])
            self.assertEqual(len(p["evidence_episode_ids"]), 1)
        self.assertEqual(result.review_payload["review_state"], self.author["review_state"])
        self.assertEqual(result.presentation_payload["review_state"], self.author["review_state"])

    def test_genuine_trajectory_path_still_requires_trusted_comparison(self):
        # Synthetic request to the unchanged non-candidate trajectory path;
        # this constructs no accepted artifact or comparison authority.
        inputs = copy.deepcopy(self.products[3]); inputs.pop("review_state")
        for action in inputs["shared_semantics"]["actions"]:
            action["eligibility"]["decision"] = "accepted"
        with self.assertRaisesRegex(SemanticCompilerInputError, "new trajectory requires"):
            run_editorial_pipeline(inputs)

    def test_paired_synthetic_mixed_and_missing_observations(self):
        for statuses in [("Yea", "Nay"), ("Nay", "Yea"), ("Yea", "Not Voting"),
                         ("Present", "Nay"), ("Yea", "Missing Evidence"), ("Present", "Not Voting")]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            for action, status in zip(inputs["members"][0]["actions"][:2], statuses):
                action["status"] = status
                if status == "Missing Evidence": action["evidence_status"] = "missing"
            result = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            pairs = [p for p in result["proposition_graph"]["propositions"] if any(o["action_id"] == "house:119:1:150" for o in p.get("action_observations", []))]
            directional = [s for s in statuses if s in {"Yea", "Nay"}]
            if not directional:
                self.assertFalse(pairs)
                continue
            pair = pairs[0]
            self.assertEqual([o["status"] for o in pair["action_observations"]], list(statuses))
            self.assertEqual(len(pair["evidence_action_ids"]), len(directional))
            self.assertEqual(pair["direction"], "mixed" if len(set(directional)) == 2 else {"Yea":"support","Nay":"opposition"}[directional[0]])

    def test_synthetic_status_and_context_controls_do_not_count(self):
        for status in ["Present", "Not Voting", "Missing Evidence"]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            inputs["members"][0]["actions"][2]["status"] = status
            if status == "Missing Evidence":
                inputs["members"][0]["actions"][2]["evidence_status"] = "missing"
            compiled = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            self.assertNotIn("house:119:1:306", compiled["action_accounting"]["behavioral_proposition_action_ids"])
        inputs = copy.deepcopy(self.products[3])
        action = inputs["shared_semantics"]["actions"][2]
        action["eligibility"]["decision"] = "context_only"
        inputs["shared_semantics"]["episodes"] = [e for e in inputs["shared_semantics"]["episodes"] if action["action_id"] not in e["action_ids"]]
        result = run_editorial_pipeline(inputs).compiled_ir
        self.assertEqual(result["members"][0]["coverage"]["eligible_substantive_actions"], len(self.author["actions"]) - 1)

    def test_readable_output_preserves_package_limits_and_actual_mechanisms(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        f = readable["members"][0]
        self.assertEqual(len(f["findings"]), 69)
        by_action = {x["action_ids"][0]: x for x in f["findings"]}
        self.assertIn("abortion", by_action["house:119:1:349"]["detail"][1])
        self.assertIn("each provision", " ".join(by_action["house:119:1:349"]["qualifications_on_both_levels"]))
        self.assertIn("5 percent", by_action["house:119:2:198"]["detail"][1])
        self.assertIsNone(f["synthesis"])

    def test_compact_is_shared_explicit_and_not_sentence_extraction(self):
        author = copy.deepcopy(self.author)
        action = author["actions"][3]
        action["meaning"] = "H.R. is an abbreviation. A later sentence describes another package mechanism."
        products = prepare(author, self.capture, ["F000477", "M001184"])
        readable = readable_candidates(author, products[0], products[2], products[-1])
        for member in readable["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == [action["action_id"]])
            self.assertIn(action["compact_description"], finding["compact"])
            self.assertNotIn("abbreviation", finding["compact"])
            self.assertIn(action["meaning"], finding["detail"])
            self.assertIn("cost-sharing", finding["compact"])
            self.assertIn("abortion", finding["compact"])
            self.assertTrue(finding["action_observations"][0]["claim_source_map"])

    def test_discovery_accounting_is_complete_but_membership_not_claimed_closed(self):
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        validate_universe_proposal(universe, self.author, self.capture, json.loads((DATA / "membership_review.json").read_text(encoding="utf-8")))
        rows = universe["candidate_dispositions"]
        expected = {f"house:119:{s}:{r}" for s, last in [(1, 362), (2, 314)] for r in range(1, last + 1)}
        self.assertEqual({r["action_id"] for r in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(sum(universe["accounting"]["counts"].values()), len(rows))
        self.assertEqual(universe["proposal_sha256"], sealed_digest(universe, "proposal_sha256"))
        self.assertFalse(universe["full_record_claim"])
        self.assertIsNone(universe["approval_receipt"])
        self.assertEqual(sum(r["after_historical_july23_boundary"] for r in rows), 31)
        recaptured = {f"house:119:2:{n}" for n in [65, 71, 72, 74, 76, 78]}
        self.assertEqual({r["action_id"] for r in rows if not r.get("historical_raw_hash_matches", True)}, recaptured)
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for row in rows:
            if row["action_id"] in recaptured:
                self.assertNotEqual(row["historical_source_identity"]["raw_sha256"], row["source"]["raw_sha256"])
                clerk = sources[row["source"]["source_id"]]
                self.assertEqual(row["source"]["raw_sha256"], clerk["raw_sha256"])
                self.assertEqual(row["source"]["governed_bytes_sha256"], sealed_digest(clerk, "governed_bytes_sha256"))
                self.assertEqual(int(clerk["metadata"]["rollcall-num"]), row["roll"])
                self.assertEqual(clerk["metadata"]["vote-question"], row["question"])
                self.assertEqual(row["historical_source_identity"]["source_id"], clerk["source_id"])
        self.assertEqual(universe["cutoff"]["end_date"], "2026-09-16")
        self.assertEqual(universe["interpretation_action_set_cutoff"], "2026-09-16")

    def test_wrong_stage_cannot_borrow_parent_passage_meaning(self):
        author = copy.deepcopy(self.author)
        author["actions"][0]["stage"] = "final_passage"
        with self.assertRaisesRegex(ValueError, "stage differs"):
            prepare(author, self.capture, ["F000477"])

    def test_compact_requires_a_bound_operative_passage(self):
        author = copy.deepcopy(self.author)
        author["actions"][0]["compact_source_refs"] = ["clerk:119:1:150"]
        with self.assertRaisesRegex(ValueError, "compact meaning"):
            prepare(author, self.capture, ["F000477"])

    def test_member_service_and_evidence_controls_remain_non_counting_in_pair(self):
        for field, value in [("service_status", "not_yet_serving"), ("service_status", "unresolved"),
                             ("evidence_status", "missing")]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            row = inputs["members"][0]["actions"][0]
            row[field] = value
            member = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            pair = next(p for p in member["proposition_graph"]["propositions"]
                        if any(o["action_id"] == row["action_id"] for o in p.get("action_observations", [])))
            self.assertIsNone(pair["action_observations"][0]["direction"])
            self.assertEqual(pair["evidence_action_ids"], ["house:119:1:151"])

    def test_membership_queue_distinguishes_work_from_exact_binding_and_unavailable_sources(self):
        u = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        rows = {r["action_id"]: r for r in u["candidate_dispositions"]}
        self.assertEqual(u["accounting"]["counts"], {"procedural_context":219, "source_unresolved":102,
            "interpreted_substantive_directional":92, "expressive_nonbinding_context":18, "exact_action_ineligible":245})
        for aid in ["house:119:2:53", "house:119:2:308", "house:119:2:313"]:
            self.assertFalse(rows[aid]["review_progress"]["exact_action_binding_unresolved"])
            self.assertTrue(rows[aid]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:72"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:72"]["disposition"], "exact_action_ineligible")
        self.assertTrue(rows["house:119:1:180"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:180"]["disposition"], "interpreted_substantive_directional")
        self.assertTrue(rows["house:119:1:199"]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:204"]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:209"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:209"]["disposition"], "interpreted_substantive_directional")
        self.assertTrue(rows["house:119:1:218"]["review_progress"]["substantive_review_performed"])
        self.assertFalse(rows["house:119:1:224"]["review_progress"]["substantive_review_performed"])
        self.assertFalse(any(r["review_progress"]["required_evidence_unavailable"] for r in rows.values()))
        self.assertEqual([aid for aid, r in rows.items() if r["review_progress"]["authoritative_source_conflict"]],
                         ["house:119:1:237"])
        unresolved = [r for r in rows.values() if r["disposition"] == "source_unresolved"]
        self.assertEqual(sum(not r["review_progress"]["substantive_review_performed"] for r in unresolved), 100)
        self.assertEqual(rows["house:119:2:310"]["disposition"], "interpreted_substantive_directional")
        self.assertEqual(rows["house:119:2:309"]["disposition"], "exact_action_ineligible")

    def test_stale_universe_cannot_replay_new_interpretations(self):
        u = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        author = copy.deepcopy(self.author); author["actions"].pop()
        with self.assertRaisesRegex(ValueError, "interpretation set differs"):
            validate_universe_proposal(u, author)
        author = copy.deepcopy(self.author); author["interpretation_action_set_cutoff"] = "2026-07-23"
        with self.assertRaisesRegex(ValueError, "cutoff differs"):
            validate_universe_proposal(u, author)
        m = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        m["records"][0]["sources"][0]["raw_sha256"] = "0" * 64
        m["review_sha256"] = sealed_digest(m, "review_sha256")
        u["membership_review_sha256"] = m["review_sha256"]
        u["candidate_dispositions"][149]["review_progress"]["shared_review_record_sha256"] = digest(m["records"][0])
        u["universe_subject_sha256"] = digest({"subject":u["subject"], "cutoff":u["cutoff"], "candidate_records":u["candidate_dispositions"]})
        u["proposal_sha256"] = sealed_digest(u, "proposal_sha256")
        with self.assertRaisesRegex(ValueError, "membership source identity differs"):
            validate_universe_proposal(u, self.author, self.capture, m)

    def test_new_versions_are_separate_observations_with_shared_limits(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        f = readable["members"][0]
        pair = next(x for x in f["findings"] if "house:119:1:145" in x["action_ids"])
        self.assertEqual(pair["action_ids"], ["house:119:1:145", "house:119:1:190"])
        self.assertIn("$10 billion", pair["action_observations"][1]["compact"])
        self.assertNotIn("$10 billion", pair["action_observations"][0]["compact"])
        fraud = next(x for x in f["findings"] if x["action_ids"] == ["house:119:2:310"])
        self.assertIn("HIPAA", " ".join(fraud["detail"]))
        self.assertIn("congressional-record:2026-09-15", fraud["source_ids"])
        self.assertIn("deletion", fraud["compact"])

    def test_resumed_priority_bindings_preserve_changed_and_retained_provisions(self):
        actions = {a["action_id"]: a for a in self.author["actions"]}
        concurrence = actions["house:119:2:53"]
        self.assertEqual(concurrence["episode_id"], actions["house:119:2:45"]["episode_id"])
        self.assertTrue({"govinfo:hr7148eas", "govinfo:pl119-37", "govinfo:hr7148eh-page-binding"}
                        <= {c["source_id"] for c in concurrence["claim_source_map"]})
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertEqual([p["pdf_page"] for p in sources["govinfo:hr7148eh-page-binding"]["page_extracts"]],
                         [4, 1132, 1152, 1153, 1181, 1235])
        sanctions = actions["house:119:2:308"]
        self.assertTrue({"govinfo:hr5334eas", "govinfo:hr5334eh", "congressional-record:2026-09-15"}
                        <= set(sanctions["compact_source_refs"]))
        # Incorporated-law claims cannot survive removal of that source binding.
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == concurrence["action_id"])["additional_source_ids"].remove("govinfo:pl119-37")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        water = next(r for r in membership["records"] if r["action_id"] == "house:119:2:313")
        self.assertEqual(water["disposition"], "exact_action_ineligible")
        self.assertIn("Clerk roll313 matches", water["binding_method"])
        self.assertTrue(water["claim_source_map"])
        self.assertNotIn(water["action_id"], actions)

    def test_real_fentanyl_pair_preserves_failed_condition_and_whole_passage(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        for member in readable["members"]:
            pair = next(f for f in member["findings"] if "house:119:1:32" in f["action_ids"])
            self.assertEqual(pair["action_ids"], ["house:119:1:32", "house:119:1:33"])
            expected = ["Yea", "Nay"] if member["member_id"] == "F000477" else ["Nay", "Nay"]
            self.assertEqual([o["status"] for o in pair["action_observations"]], expected)
            self.assertIn("It failed and was not part", pair["compact"])
            self.assertIn("govinfo:hrpt2", pair["source_ids"])
            self.assertIn("congressional-record:2025-02-06", pair["source_ids"])
            self.assertIsNone(member["synthesis"])
        for member in result.compiled_ir["members"]:
            proposition = next(p for p in member["proposition_graph"]["propositions"]
                               if any(o["action_id"] == "house:119:1:32" for o in p.get("action_observations", [])))
            self.assertEqual(proposition["proposition_type"], "notable_choice")

    def test_new_funding_and_pension_details_retain_incorporated_offsets(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        for member in readable["members"]:
            by_action = {a: f for f in member["findings"] for a in f["action_ids"]}
            pension = by_action["house:119:1:51"]
            self.assertIn("govinfo:38usc5503-2024", pension["source_ids"])
            self.assertIn("$90", " ".join(pension["detail"]))
            self.assertIn("Medicaid", pension["compact"])
            unemployment = by_action["house:119:1:68"]
            self.assertIn("govinfo:pl117-2", unemployment["source_ids"])
            self.assertIn("rescinded", unemployment["compact"])
            funding = by_action["house:119:1:70"]
            self.assertIn("govinfo:2usc901a-2024", funding["source_ids"])
            self.assertIn("sequestration", funding["compact"])
            self.assertIn("ten months at 2 percent", " ".join(funding["detail"]))


    def test_senate_origin_preserves_exact_house_action_and_rejects_measure_drift(self):
        core, _, projections, _, result = self.products
        action = next(a for a in core["actions"] if a["action_id"] == "house:119:1:104")
        self.assertEqual(action["chamber"], "house")
        self.assertEqual(action["exact_question"], "On Motion to Suspend the Rules and Pass")
        self.assertIn("govinfo:s146es", action["semantic_ir_source_ids"])
        for bill_type in [None, "hr", "sjres", "S"]:
            with self.subTest(bill_type=bill_type):
                author = copy.deepcopy(self.author)
                proposed = next(a for a in author["actions"] if a["action_id"] == action["action_id"])
                if bill_type is None:
                    proposed.pop("bill_type")
                else:
                    proposed["bill_type"] = bill_type
                with self.assertRaisesRegex(ValueError, "Clerk measure"):
                    prepare(author, self.capture, ["F000477"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == action["action_id"])["bill_number"] = 147
        with self.assertRaisesRegex(ValueError, "Clerk measure"):
            prepare(author, self.capture, ["F000477"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if action["action_id"] in f["action_ids"])
            self.assertIn("restitution", finding["compact"])
            self.assertIn("govinfo:18usc2264-2024", finding["source_ids"])
            self.assertIn("not proof of collection", " ".join(finding["qualifications_on_both_levels"]))

    def test_scott_clinical_trial_exception_is_not_inherited_by_other_questions(self):
        actions = {a["action_id"]: a for a in self.author["actions"]}
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        records = {r["action_id"]: r for r in membership["records"]}
        amendment = actions["house:119:1:79"]
        self.assertIn("solely", amendment["meaning"])
        self.assertEqual(amendment["stage"], "amendment")
        self.assertTrue({"govinfo:hrpt38", "house-rules:rcp119-1", "congressional-record:2025-03-27"}
                        <= set(amendment["compact_source_refs"]))
        for roll in [80, 81, 82, 83]:
            aid = f"house:119:1:{roll}"
            self.assertNotIn(aid, actions)
            self.assertEqual(records[aid]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[aid]["claim_source_map"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == amendment["action_id"])["additional_source_ids"].remove("house-rules:rcp119-1")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        # A medical word in a preserved consumer-product exclusion is not a new medical mechanism.
        sodium = records["house:119:1:108"]
        self.assertEqual(sodium["disposition"], "exact_action_ineligible")
        self.assertIn("govinfo:15usc2052-2024", {s["source_id"] for s in sodium["sources"]})
        self.assertNotIn(sodium["action_id"], actions)

    def test_separate_veterans_proposals_keep_each_deadline_and_existing_pension_limit(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            by_action = {aid: f for f in member["findings"] for aid in f["action_ids"]}
            for roll in [89, 90, 115, 133]:
                aid = f"house:119:1:{roll}"
                finding = by_action[aid]
                self.assertEqual(finding["action_ids"], [aid])
                self.assertIn("December 31, 2031", finding["compact"])
                self.assertIn("govinfo:38usc5503-2024", finding["source_ids"])
                self.assertIn("$90", " ".join(finding["detail"]))
            self.assertIn("one year after commencement", " ".join(by_action["house:119:1:90"]["detail"]))
            self.assertIn("two years after commencement", " ".join(by_action["house:119:1:133"]["detail"]))

    def test_senate_fentanyl_bill_does_not_absorb_the_failed_house_amendment(self):
        core, _, projections, _, result = self.products
        actions = {a["action_id"]: a for a in self.author["actions"]}
        self.assertNotEqual(actions["house:119:1:166"]["episode_id"], actions["house:119:1:33"]["episode_id"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:166" in f["action_ids"])
            self.assertEqual(finding["action_ids"], ["house:119:1:166"])
            self.assertIn("did not include the failed H.R.27 amendment", finding["compact"])
            self.assertIn("govinfo:s331es", finding["source_ids"])
            pair = next(f for f in member["findings"] if "house:119:1:32" in f["action_ids"])
            self.assertEqual(pair["action_ids"], ["house:119:1:32", "house:119:1:33"])

    def test_milcon_va_pair_retains_separate_effects_and_source_dependencies(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:180" in f["action_ids"])
            self.assertEqual(finding["action_ids"], ["house:119:1:180", "house:119:1:182"])
            observations = finding["action_observations"]
            self.assertEqual([next(a["legislative_stage"] for a in core["actions"] if a["action_id"] == o["action_id"]) for o in observations], ["amendment", "final_passage"])
            self.assertIn("netted to zero", finding["compact"])
            self.assertIn("rescinding some prior VA balances", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("not an additional $4.1 million", detail)
            self.assertIn("already set aside in December2024", detail)
            self.assertIn("except rape, incest", detail)
            self.assertIn("not a new expansion", detail)
            self.assertIn("July1,2026", detail)
            self.assertIn("July1,2027", detail)
            self.assertTrue({"house-rules:rcp119-5", "govinfo:pl115-141", "govinfo:transport-court2024"} <= set(finding["source_ids"]))
        # Losing the page/line binding must not leave an apparently replayable amendment.
        author = copy.deepcopy(self.author)
        amendment = next(a for a in author["actions"] if a["action_id"] == "house:119:1:180")
        amendment["additional_source_ids"].remove("house-rules:rcp119-5")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_stablecoin_incorporation_and_nonvote_do_not_become_generic_health_opposition(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        members = {m["member_id"]: m for m in readable["members"]}
        finding = next(f for f in members["F000477"]["findings"] if "house:119:1:200" in f["action_ids"])
        self.assertIn("reserve-shortfall", finding["compact"])
        self.assertIn("does not itself reduce", finding["compact"])
        self.assertIn("full stablecoin package", " ".join(finding["qualifications_on_both_levels"]))
        self.assertIn("govinfo:11usc507-2024", finding["source_ids"])
        self.assertFalse(any("house:119:1:200" in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:200")
        action["additional_source_ids"].remove("govinfo:11usc507-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule = records["house:119:1:203"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertIn("govinfo:hr4eas", {s["source_id"] for s in rule["sources"]})
        self.assertIn("omits the earlier separate $400-million", rule["rationale"])
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in core["actions"]})

    def test_digital_commodity_customer_pool_is_distinct_from_stablecoin_estate_priority(self):
        core, _, projections, _, result = self.products
        members = {m["member_id"]: m for m in readable_candidates(self.author, core, projections, result)["members"]}
        finding = next(f for f in members["F000477"]["findings"] if "house:119:1:199" in f["action_ids"])
        self.assertIn("customer-property pool", finding["compact"])
        self.assertTrue({"govinfo:11usc766-2024", "govinfo:11usc726-2024", "govinfo:11usc507-2024"}.issubset(finding["source_ids"]))
        self.assertIn("excess property and unpaid customer claims follow ordinary estate distribution", " ".join(finding["qualifications_on_both_levels"]))
        self.assertNotIn("house:119:1:200", finding["action_ids"])
        self.assertFalse(any("house:119:1:199" in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:199")
        action["additional_source_ids"].remove("govinfo:11usc766-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_hiv_amendment_reduces_nested_minimum_without_inheriting_whole_package(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:206" in f["action_ids"])
            self.assertIn("not the total Defense Health appropriation", finding["compact"])
            self.assertIn("did not expressly prohibit", finding["compact"])
            self.assertIn("earlier adopted amendment", finding["compact"])
            self.assertNotIn("to zero", finding["compact"])
            self.assertIn("govinfo:hr4016rh-page-binding", finding["source_ids"])
            self.assertIn("congressional-record:2025-07-16", finding["source_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{n}" for n in [204, 206, 209, 212]])
            self.assertIn("$117.988 million", finding["compact"])
            self.assertIn("govinfo:10usc401-2024", finding["source_ids"])
            self.assertIn("not the underlying authorities", finding["compact"])
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:206")
        action["additional_source_ids"].remove("govinfo:hr4016rh-page-binding")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [205, 207, 208]:
            self.assertEqual(records[f"house:119:1:{roll}"]["disposition"], "exact_action_ineligible")
            self.assertNotIn(f"house:119:1:{roll}", {a["action_id"] for a in core["actions"]})

    def test_defense_episode_preserves_country_scope_and_mixed_member_choices(self):
        core, _, projections, _, result = self.products
        readings = readable_candidates(self.author, core, projections, result)
        for member in readings["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:212" in f["action_ids"])
            observations = {o["action_id"]: o for o in finding["action_observations"]}
            self.assertEqual(list(observations), [f"house:119:1:{r}" for r in [204, 206, 209, 212]])
            expected = ["Nay"] * 4 if member["member_id"] == "F000477" else ["Yea", "Yea", "Yea", "Nay"]
            self.assertEqual([o["status"] for o in observations.values()], expected)
            ukraine = observations["house:119:1:209"]["compact"]
            self.assertIn("otherwise qualifying humanitarian medical assistance", ukraine)
            self.assertIn("not cut the whole aid account", ukraine)
            passage = observations["house:119:1:212"]["compact"]
            self.assertIn("funded military health care", passage)
            self.assertIn("restricting spending", passage)
            self.assertIn("protected civilian access", passage)
            self.assertIn("one vote on the full defense package", passage)
            detail = " ".join(observations["house:119:1:212"]["detail"])
            self.assertIn("$701 million", detail)
            self.assertIn("$14 million", detail)
            self.assertIn("not a guaranteed executed total", detail)
            self.assertIn("does not portray all2012 eligibility terms as unchanged", detail)
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:210"]["disposition"], "exact_action_ineligible")
        self.assertIn("not reach all Lebanese civilian", records["house:119:1:210"]["rationale"])
        self.assertNotIn("house:119:1:210", {a["action_id"] for a in core["actions"]})
        for aid, sid in [("house:119:1:209", "govinfo:10usc401-2024"),
                         ("house:119:1:212", "dod:reproductive-care-2022-10-20")]:
            author = copy.deepcopy(self.author)
            action = next(a for a in author["actions"] if a["action_id"] == aid)
            action["additional_source_ids"].remove(sid)
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477"])

    def test_opioid_sanctions_preserve_incorporated_waiver_and_separate_sunset(self):
        core, _, projections, _, result = self.products
        readings = readable_candidates(self.author, core, projections, result)
        for member in readings["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == ["house:119:1:220"])
            self.assertEqual(finding["action_observations"][0]["status"], "Yea")
            self.assertIn("conditional waiver", finding["compact"])
            self.assertIn("not a new treatment benefit", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("neither creates that waiver nor guarantees", detail)
            self.assertIn("does not amend the separate2334 seven-year termination", detail)
            self.assertIn("suspend the rules and pass as amended", detail)
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:220")
        action["additional_source_ids"].remove("govinfo:21usc-ch28-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [213, 214, 215, 216, 217, 219]:
            self.assertEqual(records[f"house:119:1:{roll}"]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[f"house:119:1:{roll}"]["claim_source_map"])

    def test_coast_guard_package_preserves_conditional_care_and_source_text_defect(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == ["house:119:1:218"])
            expected = "Yea" if member["member_id"] == "F000477" else "Nay"
            self.assertEqual(finding["action_observations"][0]["status"], expected)
            self.assertIn("authorizations were not appropriations", finding["compact"])
            self.assertIn("cross-reference error", finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["pilot terminates September30,2029", "already preserves medical/dental",
                             "October1,2025", "does not silently replace2519 with2520",
                             "victim’s permission", "court-martial exclusion remains",
                             "75percent federal-share ceiling"]:
                self.assertIn(boundary, detail)
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:218")
        action["additional_source_ids"].remove("govinfo:14usc-ch25-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_september_rule_accounts_for_deemed_and_tabled_resolutions_without_health_finding(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule = records["house:119:1:222"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertTrue({"govinfo:hres672eh", "govinfo:hres668eh", "govinfo:hres605eh",
                         "govinfo:hres598rh", "govinfo:hres589ih"} <= {s["source_id"] for s in rule["sources"]})
        self.assertIn("Tabling that proposal is distinct", rule["rationale"])
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in self.products[0]["actions"]})

    def test_regional_account_amendments_keep_exact_amounts_and_health_eligibility_limits(self):
        core, _, projections, _, result = self.products
        ids = [f"house:119:1:{r}" for r in range(232, 236)]
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if ids[0] in f["action_ids"])
            self.assertEqual(finding["action_ids"][:4], ids)
            self.assertEqual([o["status"] for o in finding["action_observations"][:4]],
                             ["Nay" if member["member_id"] == "F000477" else "Yea"] * 4)
            for name in ["Northern Border", "Southwest Border", "Southeast Crescent", "Great Lakes"]:
                self.assertIn(name, finding["compact"])
            for amount in ["$13,319,727", "$2,063,381", "$16,003,526", "$250,000"]:
                self.assertIn(amount, finding["compact"])
            self.assertIn("No health-only amount or loss of services", finding["compact"])
            self.assertIn("amendment failed", finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["If a commission elects", "cost-sharing conditions remain",
                             "neither is a medical allocation", "not guarantee a grant",
                             "notwithstanding40USC15751(b)"]:
                self.assertIn(boundary, detail)
            self.assertTrue({"govinfo:40usc-subtitleV-2024", "govinfo:pl118-272-regional-commissions"}
                            <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == ids[0])["additional_source_ids"].remove("govinfo:40usc-subtitleV-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_eere_amendment_binds_incorporated_household_assistance_and_nested_amounts(self):
        core, _, projections, _, result = self.products
        aid = "house:119:1:236"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertIn("not a $2.053-billion combined cut", action["meaning"])
        self.assertIn("$180million Weatherization Assistance Program", action["meaning"])
        self.assertIn("annually adjusted average-cost caps", action["meaning"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"][:5], [f"house:119:1:{r}" for r in range(232, 237)])
            observation = next(o for o in finding["action_observations"] if o["action_id"] == aid)
            self.assertEqual(observation["status"], "Nay" if member["member_id"] == "F000477" else "Yea")
            self.assertIn("$223-million administration reduction is already inside", finding["compact"])
            self.assertIn("not repeal the programs or rescind every other funding source", finding["compact"])
            self.assertTrue({"govinfo:hrpt119-213-eere", "govinfo:42usc6863-2024"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:hrpt119-213-eere")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_energy_amendment_exclusions_do_not_turn_administration_cuts_into_repeal(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [229, 230, 231]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("does not itself repeal the loan program", records["house:119:1:230"]["rationale"])
        self.assertIn("separate $150-million", records["house:119:1:231"]["rationale"])
        self.assertIn("leaving the amount unchanged", records["house:119:1:231"]["rationale"])
        self.assertIn("earlier repeal/rescission", records["house:119:1:230"]["rationale"])

    def test_drbc_exclusions_preserve_public_health_context_and_separate_funding_scopes(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule, agency = [records[f"house:119:1:{r}"] for r in [227, 228]]
        for row in [rule, agency]:
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertIn("Public-health", row["rationale"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("300,000 or more gallons", rule["rationale"])
        self.assertIn("adjacent Social Security rule", rule["rationale"])
        self.assertIn("bill-specific implementation/enforcement", rule["rationale"])
        self.assertIn("not abolition of the commission", agency["rationale"])
        self.assertIn("not patient coverage", agency["rationale"])

    def test_july_membership_reuses_consumer_definition_without_promoting_rule_votes(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:192"]["disposition"], "exact_action_ineligible")
        self.assertIn("govinfo:15usc2052-2024", {s["source_id"] for s in records["house:119:1:192"]["sources"]})
        self.assertEqual(records["house:119:1:193"]["disposition"], "exact_action_ineligible")
        for roll, version in [(195, "rh"), (198, "eh")]:
            aid = f"house:119:1:{roll}"
            self.assertEqual(records[aid]["disposition"], "procedural_context")
            self.assertIn("govinfo:hres580" + version, {s["source_id"] for s in records[aid]["sources"]})
            self.assertNotIn(aid, {a["action_id"] for a in self.products[0]["actions"]})

    def test_rescission_accounts_and_rule_amendment_have_separate_source_boundaries(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:168" in f["action_ids"])
            self.assertIn("$500 million and $400 million", finding["compact"])
            self.assertIn("unobligated", finding["compact"])
            self.assertTrue({"govinfo:hr4eh", "govinfo:pl119-4", "govinfo:pl118-47"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:1:168")["additional_source_ids"].remove("govinfo:pl118-47")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        records = {r["action_id"]: r for r in membership["records"]}
        rule = records["house:119:1:188"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertIn("congressional-record:2025-07-02", {s["source_id"] for s in rule["sources"]})
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in core["actions"]})
        self.assertIn("penalties", records["house:119:1:162"]["rationale"])
        self.assertIn("dc-council:law24-345", {s["source_id"] for s in records["house:119:1:162"]["sources"]})


    def test_energy_passage_keeps_health_riders_and_separate_unresolved_amendment(self):
        core, _, projections, _, result = self.products
        aid = "house:119:1:239"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        for boundary in ["not substituted for the House bill", "excludes molybdenum-99",
                         "does not name the separate", "previous appropriations",
                         "this Act or any other Act", "not a separate vote"]:
            self.assertIn(boundary, action["meaning"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{r}" for r in [232,233,234,235,236,239]])
            self.assertEqual([o["status"] for o in finding["action_observations"]],
                             (["Nay"] * 6 if member["member_id"] == "F000477" else ["Yea"] * 5 + ["Nay"]))
            self.assertIn("COVID-19 mask or vaccine mandates", finding["compact"])
            self.assertIn("vote does not identify a position on each", finding["compact"])
            self.assertTrue({"govinfo:hr4553eh", "energy:fy2026-oda-health-programs",
                             "govinfo:hrpt119-213-passage-health", "govinfo:42usc18649-2024"}
                            <= set(finding["source_ids"]))
        records = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]
        pending = next(r for r in records if r["action_id"] == "house:119:1:237")
        self.assertEqual(pending["disposition"], "source_unresolved")
        self.assertTrue(pending["substantive_review_performed"])
        self.assertTrue(pending["authoritative_source_conflict"])
        self.assertFalse(pending["required_evidence_unavailable"])
        self.assertNotIn(pending["action_id"], {a["action_id"] for a in core["actions"]})
        for amount in ["$1,114,784,219.49", "$1,114,734,219.49"]:
            self.assertIn(amount, pending["rationale"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("energy:fy2026-oda-health-programs")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_ndaa_care_amendments_preserve_distinct_scope_and_choice_sources(self):
        core, _, projections, _, result = self.products
        ids = ["house:119:1:245", "house:119:1:246"]
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if ids[0] in f["action_ids"])
            self.assertEqual(finding["action_ids"][:2], ids)
            self.assertEqual([o["status"] for o in finding["action_observations"][:2]],
                             ["Nay", "Nay"] if member["member_id"] == "F000477" else ["Yea", "Yea"])
            for boundary in ["referrals and duty-station changes", "sterilization condition",
                             "Two exception clauses refer to minors", "not all care or TRICARE coverage"]:
                self.assertIn(boundary, finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["purpose-bound", "without an express minor-only limit",
                             "should not be read into the separately edited", "not a claim that EFMP itself is a health insurer"]:
                self.assertIn(boundary, detail)
            self.assertTrue({"govinfo:hrpt119-255-amend13", "govinfo:hrpt119-255-amend14",
                             "govinfo:10usc1781c-2024-operative", "govinfo:10usc1079-2024-operative"}
                            <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == ids[1])["additional_source_ids"].remove("govinfo:10usc1079-2024-operative")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_ndaa_aid_choices_keep_country_and_account_scopes_and_full_episode(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:255" in f["action_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{r}" for r in [245, 246, 255, 256]])
            self.assertEqual([o["status"] for o in finding["action_observations"]],
                             ["Nay"] * 4 if member["member_id"] == "F000477" else ["Yea"] * 4)
            for boundary in ["funds made available by this bill", "not a medical-only vote",
                             "$115.317-million authorization", "not a rescission or repeal"]:
                self.assertIn(boundary, finding["compact"])
            self.assertTrue({"govinfo:pl115-91-usai-1234", "govinfo:pl116-92-usai-1244",
                             "govinfo:budget2026-ohdaca-authorities"} <= set(finding["source_ids"]))
            self.assertNotIn("house:119:1:257", finding["action_ids"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:257"]["disposition"], "exact_action_ineligible")
        self.assertIn("Taiwan, not Ukraine", records["house:119:1:257"]["rationale"])
        for aid, sid in [("house:119:1:255", "govinfo:pl115-91-usai-1234"),
                         ("house:119:1:256", "govinfo:budget2026-ohdaca-authorities")]:
            author = copy.deepcopy(self.author)
            next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(sid)
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477"])


    def test_july_passage_does_not_inherit_september_engrossment_addition(self):
        action = next(a for a in self.author["actions"] if a["action_id"] == "house:119:1:199")
        self.assertEqual(action["source_id"], "govinfo:rcp119-6-july-version")
        self.assertIn("not attributed to the July17 roll199", action["meaning"])
        self.assertNotIn("Federal Reserve digital-currency package", action["compact_description"])
        self.assertFalse(any(m["locator"].startswith("TITLE VI--") for m in action["claim_source_map"]))
        self.assertTrue({"govinfo:hrpt119-199-partsBC", "govinfo:hres707-engrossment-instruction",
                         "congressional-record:2025-07-17-3633-version"} <= set(action["additional_source_ids"]))
        core, _, projections, _, result = self.products
        members = {m["member_id"]: m for m in readable_candidates(self.author, core, projections, result)["members"]}
        finding = next(f for f in members["F000477"]["findings"] if action["action_id"] in f["action_ids"])
        self.assertIn("customer-property pool", finding["compact"])
        self.assertNotIn("Federal Reserve digital-currency package", finding["compact"])
        self.assertFalse(any(action["action_id"] in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == action["action_id"])["additional_source_ids"].remove("govinfo:hres707-engrossment-instruction")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_veterans_packages_keep_distinct_pension_dates_and_qualified_benefits(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            for roll, date in [(266, "December 31, 2032"), (269, "February 29, 2032")]:
                aid = f"house:119:1:{roll}"
                finding = next(f for f in member["findings"] if aid in f["action_ids"])
                self.assertEqual(finding["action_ids"], [aid])
                self.assertEqual(finding["action_observations"][0]["status"], "Yea")
                self.assertIn(date, finding["compact"])
                self.assertIn("$90 monthly VA pension limit for specified Medicaid-covered", finding["compact"])
                detail = " ".join(finding["detail"])
                self.assertIn("State homes", detail)
                self.assertIn("willful-concealment", detail)
                self.assertIn("govinfo:38usc5503-2024", finding["source_ids"])
            physicians = next(f for f in member["findings"] if "house:119:1:266" in f["action_ids"])
            self.assertIn("assignments remain discretionary", physicians["compact"])
            burial = next(f for f in member["findings"] if "house:119:1:269" in f["action_ids"])
            self.assertIn("seven years", burial["compact"])
            self.assertIn("not portrayed as the first possible pre 1990 medallion", " ".join(burial["detail"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:1:269")["additional_source_ids"].remove("govinfo:38usc5503-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_dc_youth_package_uses_operative_age_and_care_plan_not_title_or_predicted_harm(self):
        aid = "house:119:1:270"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_observations"][0]["status"], "Nay")
            for phrase in ["under 18 at the time of the offense", "behavioral and physical health care",
                           "without personally identifiable information", "One vote covered the whole package"]:
                self.assertIn(phrase, finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("no such Home Rule Act prohibition appears", detail)
            self.assertIn("16-2341 while the new website section is numbered 16-2340a", detail)
            self.assertIn("not a newly imposed deadline", detail)
        source = next(s for s in self.capture["sources"] if s["source_id"] == "dc-council:code-24-902-20250916")
        self.assertIn("8ed3f5ccaac32256a14f10b86418a98c93ff8c8a", source["url"])
        self.assertIn("behavioral and physical health care", source["text"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(source["source_id"])
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_dc_transfer_candidate_preserves_treatment_binding_and_separate_noncounting_controls(self):
        aid = "house:119:1:271"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertEqual(action["episode_id"], "episode:hr5140:119")
        self.assertIn("before 18 delinquent-act language is not rewritten", action["meaning"])
        self.assertIn("existing under 18 firearm-location transfer provision", action["meaning"])
        self.assertIn("16-2320(c)(1)", action["meaning"])
        self.assertIn("offenses committed on or after enactment", action["meaning"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("dc-council:code-16-2320-20250916")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll, disposition in [(268, "procedural_context"), (273, "procedural_context"),
                                  (274, "exact_action_ineligible"), (275, "exact_action_ineligible"),
                                  (282, "expressive_nonbinding_context"), (284, "procedural_context")]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], disposition)
            self.assertEqual(row["substantive_review_performed"], disposition != "procedural_context")
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("Section8’s separate resolution-of-inquiry date is not changed", records["house:119:1:273"]["rationale"])
        self.assertIn("does not itself adopt the Senate amendment", records["house:119:1:284"]["rationale"])


    def test_energy_membership_uses_original_charter_and_exact_incorporated_provisions(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for roll in [277, 278, 279]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        charter = sources["doe:ncc-charter-20191120"]
        self.assertIn("November 20, 2019", charter["text"])
        self.assertIn("solely advisory", charter["text"])
        self.assertIn("govinfo:5usc1006-2024-operative", {s["source_id"] for s in records["house:119:1:278"]["sources"]})
        grid_sources = {s["source_id"] for s in records["house:119:1:279"]["sources"]}
        self.assertIn("govinfo:16usc824-e-2024", grid_sources)
        self.assertNotIn("govinfo:16usc824e-2024", grid_sources)
        self.assertIn("public utility", sources["govinfo:16usc824-e-2024"]["text"])
        self.assertIn("Standard generator interconnection", sources["govinfo:18cfr35-28-f-2025"]["text"])
        self.assertIn("shall remain in full effect", sources["govinfo:eo13867-2024"]["text"])
        gas = records["house:119:1:304"]
        self.assertEqual(gas["disposition"], "exact_action_ineligible")
        self.assertNotIn(gas["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("50 U.S.C. 4318(c)(1)(A)", sources["govinfo:hr1949eh"]["text"])
        self.assertIn("Claims of naturalized citizens", sources["govinfo:50usc4318-2024-operative"]["text"])
        self.assertIn("§1754", sources["govinfo:50usc4813-codification-2024"]["text"])
        self.assertIn("do not silently substitute", gas["rationale"])


    def test_dc_bail_candidate_keeps_treatment_source_and_whole_package_limits(self):
        aid = "house:119:1:298"
        core, _, projections, _, result = self.products
        source_id = "dc-council:code-23-1321-20251113-operative"
        source = next(s for s in self.capture["sources"] if s["source_id"] == source_id)
        self.assertIn("88a738d1a240ebd405e0d5fcb9e0e66a01804b5a", source["url"])
        self.assertIn("Undergo medical, psychological, or psychiatric treatment", source["text"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("property or sureties can qualify", finding["compact"])
            self.assertIn("treatment option itself remains", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("removing its least-restrictive-condition standard", detail)
            self.assertIn("does not delete the treatment option itself", detail)
            self.assertIn("mismatch between section 4(a-1)", detail)
            self.assertIn("individuals charged with an offense", detail)
            self.assertIn(source_id, finding["source_ids"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(source_id)
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_november_controls_keep_procedure_expression_and_actual_institutional_actions_distinct(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll, disposition in [(286, "exact_action_ineligible"), (287, "exact_action_ineligible"),
                                  (289, "exact_action_ineligible"), (291, "procedural_context"),
                                  (292, "expressive_nonbinding_context"), (293, "procedural_context"),
                                  (297, "exact_action_ineligible"), (300, "exact_action_ineligible"),
                                  (301, "exact_action_ineligible"), (302, "procedural_context"),
                                  (303, "exact_action_ineligible"), (305, "expressive_nonbinding_context")]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], disposition)
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("does not itself pass either bill", records["house:119:1:291"]["rationale"])
        self.assertIn("not adoption", records["house:119:1:293"]["rationale"])
        self.assertIn("remove her from the Intelligence Committee", records["house:119:1:297"]["rationale"])
        self.assertIn("not the whole appropriations law", records["house:119:1:301"]["rationale"])
        self.assertIn("not adoption", records["house:119:1:302"]["rationale"])
        self.assertIn("not completion of the report", records["house:119:1:303"]["rationale"])
        self.assertIn("does not amend Medicare", records["house:119:1:305"]["rationale"])
        self.assertIn("does not assert that no underlying award", records["house:119:1:300"]["rationale"])
        self.assertIn("(h)(4)", records["house:119:1:287"]["rationale"])


    def test_rural_county_candidate_binds_medical_use_and_retains_package_limits(self):
        aid = "house:119:1:315"
        core, _, projections, _, result = self.products
        action = next(a for a in core["actions"] if a["action_id"] == aid)
        self.assertEqual(action["exact_question"], "On Motion to Suspend the Rules and Pass")
        self.assertEqual(action["legislative_stage"], "suspension_and_passage")
        self.assertEqual(action["package_component_boundary"]["boundary_type"], "whole_measure")
        self.assertEqual(next(a for a in self.author["actions"] if a["action_id"] == aid)["episode_id"], "episode:s356:119")
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("paid for by the participating county", sources["govinfo:16usc7142-2024-operative"]["text"])
        self.assertIn("twenty-five-thousand-dollar Title III grant award", sources["skamania-ems:titleiii-20230315"]["text"])
        self.assertIn("not more than 7 percent", sources["govinfo:16usc7112-2024-operative"]["text"])
        for projection in projections:
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Yea" if projection["member_id"] == "F000477" else "Nay")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("one vote on a broader package", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("September 30, 2028", detail)
            self.assertIn("September 30, 2029", detail)
            self.assertIn("pilot-program report-to-Congress requirement", detail)
            self.assertIn("does not repeal that provision", detail)
            self.assertIn("not money awarded by this bill", " ".join(finding["qualifications_on_both_levels"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("skamania-ems:titleiii-20230315")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_school_funding_measures_preserve_distinct_conditions_and_real_foushee_nonvote(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        foushee, massie = readable["members"]
        self.assertNotIn("house:119:1:312", {aid for f in foushee["findings"] for aid in f["action_ids"]})
        observation = next(a for a in projections[0]["actions"] if a["action_id"] == "house:119:1:312")
        self.assertEqual(observation["official_status"], "Not Voting")
        self.assertEqual(observation["exact_choice_effect"], "resolved_non_directional")
        self.assertIn("house:119:1:312", json.dumps(foushee["non_proposition_accounting"]))
        disclosure = next(f for f in massie["findings"] if f["action_ids"] == ["house:119:1:312"])
        prohibition = next(f for f in massie["findings"] if f["action_ids"] == ["house:119:1:313"])
        self.assertIn("not a ban on all foreign funding", disclosure["compact"])
        self.assertIn("does not specify an annual reset", " ".join(disclosure["detail"]))
        self.assertIn("reimbursement for services rendered to individuals", " ".join(disclosure["detail"]))
        self.assertIn("after one year", prohibition["compact"])
        self.assertIn("discretionary, not an automatic exemption", " ".join(prohibition["detail"]))
        self.assertIn("until contract termination", " ".join(prohibition["detail"]))
        self.assertIn("trust territories/protectorates", " ".join(disclosure["detail"]))
        for finding in [disclosure, prohibition]:
            self.assertIn("govinfo:20usc7116-2024-operative", finding["source_ids"])
            self.assertIn("govinfo:20usc7118-2024-operative", finding["source_ids"])
            self.assertIn("grants below $30,000", " ".join(finding["detail"]))

    def test_school_disclosure_candidate_requires_care_funding_source_and_preserves_limits(self):
        aid = "house:119:1:314"
        core, _, projections, _, result = self.products
        for projection in projections:
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Nay" if projection["member_id"] == "F000477" else "Yea")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("does not itself cut a grant amount", finding["compact"])
            detail = " ".join(finding["detail"])
            for limit in ["not a mental-health earmark", "grants below $30,000", "informed written parental consent",
                          "unrestricted clinical spending", "No particular school or provider is shown to lose funds"]:
                self.assertIn(limit, detail)
            self.assertIn("govinfo:20usc7118-2024-operative", finding["source_ids"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:20usc7118-2024-operative")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_december_rule_binds_dated_print_and_keeps_substitutes_procedural(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule = records["house:119:1:309"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        source_ids = {s["source_id"] for s in rule["sources"]}
        self.assertTrue({"govinfo:hres916eh", "govinfo:hr1005rh", "govinfo:hr1049rh",
                         "govinfo:hr1069rh", "govinfo:hr2965rh", "govinfo:hr4305rh",
                         "rules:rcp119-14-20251126"} <= source_ids)
        source = next(s for s in self.capture["sources"] if s["source_id"] == "rules:rcp119-14-20251126")
        self.assertEqual([p["pdf_page"] for p in source["page_extracts"]], list(range(1, 44)))
        self.assertIn("NOVEMBER 26, 2025", source["page_extracts"][0]["text"])
        self.assertIn("does not itself pass any of the six bills", rule["rationale"])
        self.assertIn("actual disclosure substitute", rule["rationale"])

    def test_december_administration_exclusions_do_not_borrow_possible_health_recipients(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [310, 311, 316]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("applies to SBA, not every Federal agency", records["house:119:1:310"]["rationale"])
        self.assertIn("does not itself repeal or suspend a health rule", records["house:119:1:311"]["rationale"])
        self.assertIn("not automatic final approval", records["house:119:1:316"]["rationale"])


    def test_december_referral_controls_do_not_promote_displayed_material_to_substantive_choices(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        actions = {a["action_id"] for a in self.products[0]["actions"]}
        for roll in [319, 321]:
            record = records[f"house:119:1:{roll}"]
            self.assertEqual(record["disposition"], "procedural_context")
            self.assertNotIn(record["action_id"], actions)
        self.assertIn("Clerk-read motion is a bare commitment", records["house:119:1:319"]["rationale"])
        self.assertIn("neither adoption of that rule nor passage", records["house:119:1:321"]["rationale"])

    def test_invest_amendments_bind_exact_print_and_designee_without_borrowing_package_membership(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        actions = {a["action_id"] for a in self.products[0]["actions"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for roll in [325, 326, 327, 328]:
            record = records[f"house:119:1:{roll}"]
            self.assertEqual(record["disposition"], "exact_action_ineligible")
            self.assertNotIn(record["action_id"], actions)
            self.assertTrue(record["claim_source_map"])
        print_source = sources["rules:rcp119-15-20251202-section307"]
        self.assertEqual([p["pdf_page"] for p in print_source["page_extracts"]], [1, 63, 64])
        self.assertIn("DECEMBER 2, 2025", print_source["page_extracts"][0]["text"])
        self.assertIn("Garcia’s designee", records["house:119:1:326"]["rationale"])
        passage = records["house:119:1:328"]
        self.assertIn("adult-protective-service", passage["rationale"])
        self.assertIn("health/long-term-care distribution tax exception", passage["rationale"])
        self.assertIn("govinfo:42usc1397k-2024-page", {s["source_id"] for s in passage["sources"]})

    def test_water_energy_and_land_exclusions_retain_exact_health_adjacent_limits(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        action_ids = {a["action_id"] for a in self.products[0]["actions"]}
        for roll in [330, 332, 334, 335, 336]:
            record = records[f"house:119:1:{roll}"]
            self.assertEqual(record["disposition"], "exact_action_ineligible")
            self.assertTrue(record["substantive_review_performed"])
            self.assertTrue(record["claim_source_map"])
            self.assertNotIn(record["action_id"], action_ids)
        self.assertIn("toxic pollutant injurious to human health", sources["govinfo:33usc1342-2024-water-boundary"]["text"])
        self.assertIn("imminent and substantial danger to human health", sources["govinfo:hr3898eh"]["text"])
        self.assertIn("without striking that existing exception", records["house:119:1:330"]["rationale"])
        self.assertIn("only on the stated necessity finding", records["house:119:1:334"]["rationale"])
        self.assertIn("covenant warranting", sources["govinfo:42usc9620-2024-operative"]["text"])
        self.assertIn("not claim the parcel is uncontaminated", records["house:119:1:336"]["rationale"])
        self.assertIn("Direct patient care", sources["govinfo:38usc7422-2024-operative"]["text"])
        self.assertIn("unexamined agreement term", records["house:119:1:332"]["rationale"])
        rule = records["house:119:1:331"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertNotIn(rule["action_id"], action_ids)
        self.assertIn("no deemed passage", rule["rationale"])

    def test_minor_procedure_candidate_preserves_exceptions_and_unoffered_amendment_boundary(self):
        aid = "house:119:1:351"
        core, _, projections, _, result = self.products
        for projection in projections:
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Nay" if projection["member_id"] == "F000477" else "Yea")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("under 18", finding["compact"])
            self.assertIn("could not be prosecuted", finding["compact"])
            detail = " ".join(finding["detail"])
            for phrase in ["precocious puberty", "mental, behavioral or emotional", "expressly not offered",
                           "not the formal bare motion", "preserves that drafting mismatch", "separate H.R. 498"]:
                self.assertIn(phrase, detail)
            self.assertIn("govinfo:18usc116-2024-operative", finding["source_ids"])
            self.assertIn("govinfo:hrpt119-411-roy", finding["source_ids"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:18usc116-2024-operative")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_child_placement_candidate_preserves_removed_and_retained_care_provisions(self):
        aid = "house:119:1:340"
        core, _, projections, _, result = self.products
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for projection in projections:
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Nay" if projection["member_id"] == "F000477" else "Yea")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            for phrase in ["12 or older", "monthly-review", "while retaining"]:
                self.assertIn(phrase, finding["compact"])
            detail = " ".join(finding["detail"])
            for phrase in ["A conviction is therefore not required", "sponsor clause’s own conviction requirement",
                           "monthly secure-placement review", "qualified access-to-counsel", "section642(g)(2)",
                           "formal motion was bare recommittal", "January 2025 Laken Riley Act"]:
                self.assertIn(phrase, detail)
            self.assertTrue({"govinfo:6usc279-2024-operative", "govinfo:8usc1232-2024-care-placement",
                             "govinfo:pl119-1-section2"} <= set(finding["source_ids"]))
        self.assertIn("health care", sources["govinfo:8usc1522-2024-child-services"]["text"])
        self.assertIn("mental well-being", sources["govinfo:8usc1232-2024-care-placement"]["text"])
        self.assertIn("other gang-related markings", sources["govinfo:hr4371eh"]["text"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:8usc1232-2024-care-placement")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_december_environment_choices_keep_health_limits_and_exact_procedural_effects(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        action_ids = {a["action_id"] for a in self.products[0]["actions"]}
        for roll in [342, 345, 346, 347, 352, 353, 354, 356, 358, 360]:
            record = records[f"house:119:1:{roll}"]
            self.assertEqual(record["disposition"], "exact_action_ineligible")
            self.assertTrue(record["substantive_review_performed"])
            self.assertTrue(record["claim_source_map"])
            self.assertNotIn(record["action_id"], action_ids)
        self.assertIn("human health or property", records["house:119:1:354"]["rationale"])
        self.assertIn("offered by Roy", records["house:119:1:353"]["rationale"])
        self.assertIn("renumbered, not newly enacted", records["house:119:1:356"]["rationale"])
        self.assertIn("without further appropriations", records["house:119:1:358"]["rationale"])
        self.assertIn("Mexican wolf", records["house:119:1:360"]["rationale"])
        self.assertEqual([p["pdf_page"] for p in sources["govinfo:hr4776rh-amendment-pages"]["page_extracts"]], [5, 23, 26, 29])
        self.assertIn("public health and safety", sources["govinfo:30usc1245-2024-operative"]["text"])
        self.assertIn("125 percent", sources["govinfo:pl119-21-section60026"]["text"])
        self.assertIn("§42.", sources["govinfo:30usc42-2024-operative"]["text"])
        for roll in [338, 344]:
            record = records[f"house:119:1:{roll}"]
            self.assertEqual(record["disposition"], "procedural_context")
            self.assertNotIn(record["action_id"], action_ids)
            self.assertTrue(record["claim_source_map"])
        self.assertIn("does not itself pass any of the six", records["house:119:1:338"]["rationale"])
        self.assertIn("Sections4–5 also deem", records["house:119:1:344"]["rationale"])

    def test_premium_credit_extension_uses_adopted_substitute_and_updated_baseline(self):
        aid = "house:119:2:11"
        core, _, projections, _, result = self.products
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for projection in projections:
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Yea" if projection["member_id"] == "F000477" else "Nay")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("through 2028", finding["compact"])
            self.assertIn("repayment changes enacted in 2025", finding["compact"])
            detail = " ".join(finding["detail"])
            for phrase in ["November 12, 2025 substitute", "not cap every plan’s price", "does not guarantee a positive credit",
                           "removal of the cap on repayment", "not a vote to create or repeal the entire ACA"]:
                self.assertIn(phrase, detail)
            self.assertTrue({"govinfo:26usc36B-2024-operative", "govinfo:pl119-21-sections71301-71305",
                             "congressional-record:2025-11-12-1834-substitute"} <= set(finding["source_ids"]))
        for roll in [4, 10]:
            control = records[f"house:119:2:{roll}"]
            self.assertEqual(control["disposition"], "procedural_context")
            self.assertNotIn(control["action_id"], {a["action_id"] for a in core["actions"]})
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:pl119-21-sections71301-71305")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_erisa_welfare_scope_does_not_leak_into_pension_only_amendment(self):
        aid = "house:119:2:31"
        core, _, projections, _, result = self.products
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [26, 29]:
            self.assertEqual(records[f"house:119:2:{roll}"]["disposition"], "exact_action_ineligible")
            self.assertNotIn(f"house:119:2:{roll}", {a["action_id"] for a in core["actions"]})
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            observation = next(a for p in projections if p["member_id"] == member["member_id"] for a in p["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Nay" if member["member_id"] == "F000477" else "Yea")
            detail = " ".join(finding["detail"])
            for phrase in ["covered health/welfare plans", "documented tie-breaking exception", "governmental plans",
                           "January 1, 2026", "January 1, 2027", "illustrations, not promised returns", "one whole-bill choice"]:
                self.assertIn(phrase, detail)
            self.assertTrue({"govinfo:hr2988eh", "govinfo:29usc1002-217-scope", "govinfo:29usc1101-217-scope"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:29usc1002-217-scope")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_7148_passage_does_not_revote_later_engrossment_additions(self):
        aid = "house:119:2:45"
        core, _, projections, _, result = self.products
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertEqual(action["source_id"], "govinfo:hr7148ih-passage45-scope")
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid, "house:119:2:53"])
            detail = " ".join(finding["detail"])
            for phrase in ["introduced divisions A, B, D, E and F", "Both separately offered PartB amendments were rejected",
                           "not treated as a second roll45 choice", "later concurrence is a separate choice"]:
                self.assertIn(phrase, detail)
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:hres1014eh")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_special_purpose_financing_requires_care_classification_and_keeps_credit_limits(self):
        aid = "house:119:2:32"
        core, _, projections, _, result = self.products
        required = {"govinfo:hr5763eh", "govinfo:15usc696-224-operative",
                    "sba:sop50108-20250601-special-purpose", "sba:notice5000-872764-new-business"}
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            observation = next(a for p in projections if p["member_id"] == member["member_id"] for a in p["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Yea")
            self.assertTrue(required <= set(finding["source_ids"]))
            detail = " ".join(finding["detail"])
            for phrase in ["hospitals, surgery centers, urgent-care centers", "at least 15 percent",
                           "licensed and to provide healthcare", "additional borrower contribution",
                           "not treated as enactment", "not a separate vote limited to health facilities"]:
                self.assertIn(phrase, detail)
        for missing in ["sba:sop50108-20250601-special-purpose", "govinfo:15usc696-224-operative"]:
            author = copy.deepcopy(self.author)
            next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(missing)
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477", "M001184"])

    def test_pregnancy_information_keeps_scope_and_driving_amendment_stays_separate(self):
        core, _, projections, _, result = self.products
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        driving = records["house:119:2:43"]
        self.assertEqual(driving["disposition"], "exact_action_ineligible")
        self.assertNotIn("house:119:2:43", {a["action_id"] for a in core["actions"]})
        self.assertTrue({"govinfo:49usc30111-24220-and-standards", "govinfo:hr7148ih-reference-scope"} <= {s["source_id"] for s in driving["sources"]})
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:2:47" in f["action_ids"])
            self.assertEqual(finding["action_ids"], ["house:119:2:47"])
            observation = next(a for p in projections if p["member_id"] == member["member_id"] for a in p["actions"] if a["action_id"] == "house:119:2:47")
            self.assertEqual(observation["official_status"], "Nay" if member["member_id"] == "F000477" else "Yea")
            detail = " ".join(finding["detail"])
            for phrase in ["Title IV student-aid", "bare recommittal", "at least once each academic year",
                           "handbooks if any", "carrying to term and parenting after birth",
                           "does not itself prohibit an institution from providing other information",
                           "does not establish enactment"]:
                self.assertIn(phrase, detail)
            self.assertTrue({"govinfo:hr6359eh", "govinfo:20usc1688-operative", "govinfo:hres1009eh"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:2:47")["additional_source_ids"].remove("govinfo:20usc1688-operative")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_project_exception_binding_stays_unresolved_without_inferred_funding_cut(self):
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        row = next(r for r in universe["candidate_dispositions"] if r["action_id"] == "house:119:2:44")
        self.assertEqual(row["disposition"], "source_unresolved")
        self.assertTrue(row["review_progress"]["substantive_review_performed"])
        self.assertTrue(row["review_progress"]["exact_action_binding_unresolved"])
        self.assertFalse(row["review_progress"]["required_evidence_unavailable"])
        self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        bound = {s["source_id"] for s in row["sources"]}
        self.assertTrue({"house:7148-jan20-1252-preface", "govinfo:hr7148ih-preface-pages",
                         "govinfo:hr7148ih-explicit-care-project-appropriations"} <= bound)
        for member in readable_candidates(self.author, self.products[0], self.products[2], self.products[4])["members"]:
            self.assertFalse(any(row["action_id"] in f["action_ids"] for f in member["findings"]))

    def test_mining_rule_and_passage_share_exact_substitute_without_health_projection(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        rh = sources["govinfo:hr4090rh"]["text"]
        eh = sources["govinfo:hr4090eh"]["text"]
        rh = rh[rh.index("SECTION 1."):].split("Union Calendar No.")[0].strip()
        eh = eh[eh.index("SECTION 1."):eh.index("Passed the House")].strip()
        self.assertEqual(rh, eh)
        self.assertEqual(records["house:119:2:52"]["disposition"], "procedural_context")
        for aid in ["house:119:2:52", "house:119:2:55"]:
            self.assertTrue({"govinfo:hr4090rh", "govinfo:43usc31l-operative"} <= {s["source_id"] for s in records[aid]["sources"]})
        for aid in ["house:119:2:48", "house:119:2:55"]:
            self.assertEqual(records[aid]["disposition"], "exact_action_ineligible")
        for projection in self.products[2]:
            self.assertFalse({"house:119:2:48", "house:119:2:52", "house:119:2:55"} & {a["action_id"] for a in projection["actions"]})

    def test_veterans_payment_offsets_remain_distinct_and_nonvoting_is_not_opposition(self):
        core, _, projections, _, result = self.products
        members = {m["member_id"]: m for m in readable_candidates(self.author, core, projections, result)["members"]}
        for roll, date in [(49, "July 31, 2033"), (50, "February 28, 2033")]:
            aid = f"house:119:2:{roll}"
            finding = next(f for f in members["F000477"]["findings"] if aid in f["action_ids"])
            detail = " ".join(finding["detail"])
            for phrase in [date, "$90 per month", "neither spouse nor child", "State home", "January 31, 2033"]:
                self.assertIn(phrase, detail)
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("govinfo:pl119-43-pension-expiry", finding["source_ids"])
            self.assertFalse(any(aid in f["action_ids"] for f in members["M001184"]["findings"]))
            observation = next(a for p in projections if p["member_id"] == "M001184" for a in p["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], "Not Voting")
        for roll in [49, 50]:
            author = copy.deepcopy(self.author)
            next(a for a in author["actions"] if a["action_id"] == f"house:119:2:{roll}")["additional_source_ids"].remove("govinfo:pl119-43-pension-expiry")
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477", "M001184"])

    def test_failed_rule_and_later_passages_keep_complete_versions_without_health_findings(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertEqual(sources["clerk:119:2:60"]["metadata"]["vote-result"], "Failed")
        self.assertEqual(records["house:119:2:60"]["disposition"], "procedural_context")
        for roll in [58, 64, 67, 70]:
            self.assertEqual(records[f"house:119:2:{roll}"]["disposition"], "exact_action_ineligible")
        for roll, bill in [(64, "3617"), (67, "261")]:
            rh = sources[f"govinfo:hr{bill}rh"]["text"]
            eh = sources[f"govinfo:hr{bill}eh"]["text"]
            rh = rh[rh.index("SECTION 1."):].split("Union Calendar No.")[0].strip()
            if bill == "261":
                # The RH title-amendment instruction follows the operative sections.
                rh, title_instruction = rh.split("Amend the title so as to read:", 1)
                self.assertIn(title_instruction.strip().removeprefix("``A bill ").removesuffix("''.").removesuffix(".").lower(),
                              eh[eh.rindex("AN ACT"):].lower())
            eh = eh[eh.index("SECTION 1."):eh.index("Passed the House")].strip()
            self.assertEqual(rh.strip(), eh)
            self.assertIn("govinfo:hres1057eh", {s["source_id"] for s in records[f"house:119:2:{roll}"]["sources"]})
        self.assertEqual([p["pdf_page"] for p in sources["house:rcp119-18-complete"]["page_extracts"]], list(range(1, 8)))
        required = {"house:rcp119-18-complete", "govinfo:26usc5845-firearm", "govinfo:26usc4181-4182-operative"}
        for roll in [60, 70]:
            self.assertTrue(required <= {s["source_id"] for s in records[f"house:119:2:{roll}"]["sources"]})
        self.assertIn("congressional-record:2026-02-12-device-health-context", {s["source_id"] for s in records["house:119:2:70"]["sources"]})
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in [58, 60, 64, 67, 70]} & {a["action_id"] for a in projection["actions"]})

    def test_election_substitute_and_bare_commitment_keep_exact_membership_boundaries(self):
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        rows = {r["action_id"]: r for r in universe["candidate_dispositions"]}
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for roll, disposition in [(62, "procedural_context"), (68, "procedural_context"), (69, "exact_action_ineligible")]:
            row = rows[f"house:119:2:{roll}"]
            self.assertEqual(row["disposition"], disposition)
            self.assertEqual(row["review_progress"]["substantive_review_performed"], roll == 69)
            self.assertFalse(row["review_progress"]["required_evidence_unavailable"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertEqual(sources["govinfo:s1383eah"]["text_version"], "EAH")
        self.assertEqual([p["pdf_page"] for p in sources["house:rcp119-19-complete"]["page_extracts"]], list(range(1, 33)))
        for roll in [62, 69]:
            self.assertTrue({"govinfo:s1383eah", "govinfo:hres1057eh", "govinfo:hrpt119-493",
                             "house:rcp119-19-complete", "govinfo:52usc20502-20511-operative",
                             "govinfo:42usc1320b-7-save-and-benefit-boundary", "govinfo:52usc20102-2024-operative"}
                            <= {s["source_id"] for s in records[f"house:119:2:{roll}"]["sources"]})
        self.assertIn("prior to providing the form", sources["govinfo:s1383eah"]["text"])
        self.assertIn("will not affect the amount of assistance", sources["govinfo:52usc20502-20511-operative"]["text"])
        self.assertIn("administrative (non-criminal) immigration enforcement", sources["govinfo:42usc1320b-7-save-and-benefit-boundary"]["text"])
        self.assertEqual(sources["clerk:119:2:68"]["metadata"]["vote-result"], "Failed")
        self.assertIn("separate earlier insertion", records["house:119:2:68"]["rationale"])
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in [62, 68, 69]} & {a["action_id"] for a in projection["actions"]})

    def test_housing_package_keeps_existing_income_policy_and_whole_member_choices(self):
        aid = "house:119:2:57"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertEqual(action["stage"], "suspension_and_passage")
        required = {"hud:2024-published-vash-income", "irs:revenue-procedure2024-38-vash",
                    "govinfo:1437a-income-definitions-2024", "govinfo:24cfr984103-welfare-2025"}
        self.assertTrue(required <= set(action["additional_source_ids"]))
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("Applicability date: August 13, 2024", sources["hud:2024-published-vash-income"]["text"])
        self.assertNotIn("PENDING PUBLICATION", sources["hud:2024-published-vash-income"]["text"])
        self.assertIn("included for purposes of calculating the total tenant payment", sources["hud:2024-published-vash-income"]["text"])
        self.assertIn("on or after October 24, 2024", sources["irs:revenue-procedure2024-38-vash"]["text"])
        for member, status in [("F000477", "Yea"), ("M001184", "Nay")]:
            projection = next(p for p in self.products[2] if p["member_id"] == member)
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], status)
            readable = next(m for m in readable_candidates(self.author, self.products[0], self.products[2], self.products[4])["members"] if m["member_id"] == member)
            finding = next(f for f in readable["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertTrue(required <= set(finding["source_ids"]))
            self.assertIn("not a promised reduction in rent", " ".join(finding["detail"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("hud:2024-published-vash-income")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477", "M001184"])

    def test_housing_qualifications_are_bound_without_repairing_printed_text(self):
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        action = next(a for a in self.author["actions"] if a["action_id"] == "house:119:2:57")
        eh = sources["govinfo:hr6644eh"]["text"]
        for phrase in ["defined in section 215(a)(7)", "(8) Small-scale housing", "written permission from the resident"]:
            self.assertIn(phrase.lower(), eh.lower())
        self.assertIn("(b) Termination of tenancy", sources["govinfo:42usc12755-2024-housing"]["text"])
        self.assertIn("(c) Maintenance and replacement", sources["govinfo:42usc12755-2024-housing"]["text"])
        self.assertIn("promissory note", sources["govinfo:42usc1474-2024-housing"]["text"])
        welfare = sources["govinfo:24cfr984103-welfare-2025"]["text"]
        for exclusion in ["(viii) Amounts for health care", "(x) Supplemental Security Income", "(xi) Child-only or non-needy TANF"]:
            self.assertIn(exclusion, welfare)
        for phrase in ["not a doubled grant ceiling", "narrowly defined welfare cash assistance",
                       "not for every government program", "seven years after enactment",
                       "does not silently correct", "not a new housing-services appropriation"]:
            self.assertIn(phrase, action["meaning"])
        rows = {r["action_id"]: r for r in json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))["candidate_dispositions"]}
        self.assertEqual(rows["house:119:2:57"]["disposition"], "interpreted_substantive_directional")
        self.assertEqual(rows["house:119:2:224"]["disposition"], "source_unresolved")
        self.assertNotIn("house:119:2:224", {a["action_id"] for a in self.products[0]["actions"]})

    def test_march4_5_controls_and_exclusions_keep_exact_questions_and_source_boundaries(self):
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        records = {r["action_id"]: r for r in membership["records"]}
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        rows = {r["action_id"]: r for r in universe["candidate_dispositions"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        expected = {79: "procedural_context", 80: "procedural_context", 81: "exact_action_ineligible",
                    82: "exact_action_ineligible", 83: "procedural_context", 84: "expressive_nonbinding_context",
                    85: "exact_action_ineligible", 86: "procedural_context"}
        for n, disposition in expected.items():
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], disposition)
            self.assertTrue(rows[f"house:119:2:{n}"]["exact_action_source_binding"]["complete"])
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in expected} & {a["action_id"] for a in projection["actions"]})
        self.assertEqual(sources["clerk:119:2:83"]["metadata"]["vote-question"], "On Motion to Refer")
        self.assertIn("Mr. Garbarino of New York moves to refer the resolution to the Committee on Ethics.",
                      sources["congressional-record:2026-03-04-ethics-referral"]["text"])
        self.assertIn("This paragraph shall not apply", sources["govinfo:s723es"]["text"])
        self.assertIn("Act or other law restricting access to", sources["govinfo:25cfr150303-2025-access"]["text"])
        self.assertIn("no-force-authorization", records["house:119:2:85"]["rationale"])
        self.assertEqual(sources["clerk:119:2:85"]["metadata"]["vote-result"], "Failed")
        self.assertFalse(any("Page Not Found" in s.get("text", "")[:80] for s in self.capture["sources"][-20:]))

    def test_march17_19_membership_keeps_nih_benefit_and_failed_suspension_boundaries(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for n in [88, 89, 93, 94, 95, 96]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[f"house:119:2:{n}"]["substantive_review_performed"])
        for n in [90, 91, 92]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "procedural_context")
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in range(88, 97)} & {a["action_id"] for a in projection["actions"]})
        self.assertIn("human pathogens", sources["govinfo:15usc1511d-2024-marine"]["text"])
        self.assertIn("pet food", sources["govinfo:hr4294eh"]["text"])
        self.assertIn("National Institutes of Health may use $5,000,000", sources["govinfo:15usc638-2024-small-research"]["text"])
        self.assertIn("commercialization", records["house:119:2:89"]["rationale"])
        self.assertIn("not newly appropriated", records["house:119:2:89"]["rationale"])
        for sid in ["govinfo:8usc1611-2024-benefit-definition", "govinfo:8usc1621-2024-benefit-definition"]:
            self.assertIn("welfare, health, disability", sources[sid]["text"])
        self.assertIn("1128(a)(2)(J)", sources["govinfo:hr1958eh"]["text"])
        self.assertIn("without silently correcting", records["house:119:2:94"]["rationale"])
        self.assertEqual(sources["clerk:119:2:95"]["metadata"]["vote-result"], "Failed")
        self.assertEqual(sources["govinfo:hjres139rh"]["text_version"], "RH")
        self.assertIn("fifth year beginning after ratification", sources["congressional-record:2026-03-18-hjres139"]["text"])
        self.assertIn("despite a simple majority", records["house:119:2:95"]["rationale"])
        self.assertNotIn("govinfo:hjres139eh", sources)

    def test_hr7744_care_package_retains_existing_conditions_and_single_shared_choice(self):
        aid = "house:119:2:87"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertEqual((action["episode_id"], action["stage"]), ("episode:hr7744:119", "final_passage"))
        self.assertIn("pregnant or in post-delivery recuperation", sources["govinfo:hr7744eh"]["text"])
        self.assertIn("In no case may restraints be used on a woman who is in active labor or delivery",
                      sources["govinfo:hr7744eh"]["text"])
        self.assertIn("has a current, valid, and unrestricted", sources["govinfo:pl116-136-16005-health-license"]["text"])
        for phrase in ["one whole-package vote", "not guaranteed", "least restrictive", "no-private-right",
                       "not generally legalize", "license-portability", "not the passed EH", "House passage alone"]:
            self.assertIn(phrase, action["meaning"])
        f, m = [{a["action_id"]: a for a in p["actions"]} for p in self.products[2]]
        self.assertEqual((f[aid]["official_status"], m[aid]["official_status"]), ("Nay", "Yea"))
        self.assertEqual(f[aid]["action_core_sha256"], m[aid]["action_core_sha256"])
        rendered = readable_candidates(self.author, self.products[0], self.products[2], self.products[-1])
        for member in rendered["members"]:
            findings = [f for f in member["findings"] if aid in f["action_ids"]]
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["action_ids"], [aid])
        for sid in ["govinfo:pl116-136-16005-health-license", "cbp:2021-pregnant-postpartum-custody-public-mirror"]:
            changed = copy.deepcopy(self.capture)
            source = next(s for s in changed["sources"] if s["source_id"] == sid)
            source["text"] = "Missing operative care authority"
            source["governed_bytes_sha256"] = sealed_digest(source, "governed_bytes_sha256")
            with self.assertRaisesRegex(ValueError, "passage"):
                prepare(self.author, changed, ["F000477", "M001184"])

    def test_hr8029_verified_same_body_remains_separate_from_rule_and_recommittal(self):
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        def body(sid):
            text = sources[sid]["text"]
            return text[text.index("SEC. 2. TABLE OF CONTENTS."):text.index("Passed the House of Representatives")]
        self.assertEqual(body("govinfo:hr7744eh"), body("govinfo:hr8029eh"))
        self.assertNotEqual(sources["govinfo:hr7744eh"]["raw_sha256"], sources["govinfo:hr8029eh"]["raw_sha256"])
        actions = {a["action_id"]: a for a in self.author["actions"]}
        self.assertNotEqual(actions["house:119:2:87"]["episode_id"], actions["house:119:2:104"]["episode_id"])
        self.assertIn("March26", actions["house:119:2:104"]["meaning"])
        floor = sources["congressional-record:2026-03-26-hr8029"]["text"]
        self.assertIn("Ms. DeLauro of Connecticut moves to recommit the bill H.R. 8029 to the Committee on Appropriations.", floor)
        self.assertIn("If the House rules permitted", floor)
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for n in [98, 99, 100, 103, 106, 107, 108]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "procedural_context")
        self.assertEqual(records["house:119:2:102"]["disposition"], "expressive_nonbinding_context")
        self.assertIn("real deemed-concurrence effect", records["house:119:2:108"]["rationale"])
        self.assertIn("Rules Committee Print 119-21", sources["govinfo:hres1142eh"]["text"])
        for key in ["metadata", "member_records", "party_totals"]:
            self.assertEqual(sources["clerk:119:2:106"][key], sources["clerk:119:2:106:continuation-recapture"][key])
        self.assertNotEqual(sources["clerk:119:2:106"]["raw_sha256"], sources["clerk:119:2:106:continuation-recapture"]["raw_sha256"])
        readable = readable_candidates(self.author, self.products[0], self.products[2], self.products[-1])
        for member in readable["members"]:
            for n in [87, 104]:
                findings = [f for f in member["findings"] if f"house:119:2:{n}" in f["action_ids"]]
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]["action_ids"], [f"house:119:2:{n}"])
        observations = [{a["action_id"]: a for a in p["actions"]}["house:119:2:104"] for p in self.products[2]]
        self.assertEqual([o["official_status"] for o in observations], ["Nay", "Yea"])
        self.assertEqual(observations[0]["action_core_sha256"], observations[1]["action_core_sha256"])

    def test_sol_slice_preserves_suspension_failure_and_noncounting_boundaries(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertEqual(sources["clerk:119:2:72"]["metadata"]["vote-result"], "Failed")
        self.assertIn("FAILED", records["house:119:2:72"]["rationale"])
        self.assertIn("air-medical", records["house:119:2:72"]["rationale"])
        for projection in self.products[2]:
            self.assertFalse({f"house:119:2:{n}" for n in [65, 71, 72, 74, 76]} & {a["action_id"] for a in projection["actions"]})
        for n in [65, 71, 72, 76]:
            self.assertEqual(records[f"house:119:2:{n}"]["disposition"], "exact_action_ineligible")
        self.assertEqual(records["house:119:2:74"]["disposition"], "procedural_context")

    def test_sol_rebate_repeal_uses_shared_whole_choice_and_retained_program(self):
        aid = "house:119:2:78"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertIn("less than 150 percent", sources["govinfo:pl117-169-home-rebates-training-codes"]["text"])
        self.assertIn("Section 50123", sources["govinfo:pl119-21-50402-energy-rescissions"]["text"])
        self.assertIn("unobligated balances", sources["govinfo:hr4758eh"]["text"])
        for member, status in [("F000477", "Nay"), ("M001184", "Yea")]:
            projection = next(p for p in self.products[2] if p["member_id"] == member)
            observation = next(a for a in projection["actions"] if a["action_id"] == aid)
            self.assertEqual(observation["official_status"], status)
            readable = next(m for m in readable_candidates(self.author, self.products[0], self.products[2], self.products[4])["members"] if m["member_id"] == member)
            finding = next(f for f in readable["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            for boundary in ["already rescinded", "is not repealed", "no direct-spending effect", "House passage alone", "less than 150 percent"]:
                self.assertIn(boundary, " ".join(finding["detail"]))
        broken = copy.deepcopy(self.author)
        next(a for a in broken["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:pl119-21-50402-energy-rescissions")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(broken, self.capture, ["F000477", "M001184"])

    def test_farm_passage_appends_whole_choice_without_merging_amendment_positions(self):
        aid = "house:119:2:154"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertEqual((action["episode_id"], action["stage"]), ("episode:hr7567:119", "final_passage"))
        rendered = readable_candidates(self.author, self.products[0], self.products[2], self.products[-1])
        statuses = {"F000477": ["Yea", "Yea", "Nay", "Nay"], "M001184": ["Yea", "Yea", "Yea", "Yea"]}
        for member in rendered["members"]:
            matches = [f for f in member["findings"] if aid in f["action_ids"]]
            self.assertEqual(len(matches), 1)
            finding = matches[0]
            self.assertEqual(finding["action_ids"], [f"house:119:2:{n}" for n in [145, 146, 151, 154]])
            self.assertEqual([o["status"] for o in finding["action_observations"]], statuses[member["member_id"]])
            passage = finding["action_observations"][-1]
            for boundary in ["entire exact farm package", "failed soda", "does not restore SNAP-Ed", "one authorization",
                             "AND annual TitleII funds", "prospective engrossment", "House passage is not enactment"]:
                self.assertIn(boundary, " ".join(passage["detail"]))
            self.assertIn("separate component positions", passage["compact"])
        projected = [next(a for a in p["actions"] if a["action_id"] == aid) for p in self.products[2]]
        self.assertEqual(projected[0]["action_core_sha256"], projected[1]["action_core_sha256"])

    def test_farm_passage_cannot_lose_current_law_or_care_authority(self):
        for sid in ["govinfo:pl119-69-school-milk", "govinfo:pl119-21-farm-nutrition-current-law",
                    "govinfo:7usc1990a-2024-rural-refinancing", "govinfo:7usc1736o-1-2024-mcgovern-dole"]:
            changed = copy.deepcopy(self.capture)
            source = next(s for s in changed["sources"] if s["source_id"] == sid)
            source["text"] = "Missing material incorporated authority"
            source["governed_bytes_sha256"] = sealed_digest(source, "governed_bytes_sha256")
            with self.assertRaisesRegex(ValueError, "passage"):
                prepare(self.author, changed, ["F000477", "M001184"])

if __name__ == "__main__":
    unittest.main()
