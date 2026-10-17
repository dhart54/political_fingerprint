"""Mutation checks at the new seed's actual evidence and isolation boundaries."""
import copy
import unittest

from scripts.validate_infrastructure_candidate_seed import (
    DATA, read, validate_inputs, validate_generated,
)
from scripts.prepare_shared_domain_candidate import prepare
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest


class InfrastructureCandidateSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = [read(DATA / f"{n}.json") for n in
                      ["authoring", "sources", "universe_proposal", "membership_review"]]

    def test_final_bytes_and_exact_member_reuse(self):
        receipt = validate_generated(*self.values)
        self.assertEqual(receipt["member_observations"], 6)
        self.assertTrue(receipt["byte_identical_generated_replay"])

    def test_resealed_governed_source_cannot_drop_operative_witness(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        source = next(s for s in capture["sources"] if s["source_id"] == "govinfo:hr192eh")
        source["text"] = "Amtrak Executive Bonus Disclosure Act"
        source["governed_bytes_sha256"] = sealed_digest(source, "governed_bytes_sha256")
        with self.assertRaisesRegex(ValueError, "claim passage absent"):
            prepare(author, capture, ["F000477", "M001184"])

    def test_member_contamination_in_current_authoring_is_rejected(self):
        values = copy.deepcopy(self.values)
        values[0]["actions"][0]["meaning"] += " Foushee voted Yea."
        with self.assertRaisesRegex(ValueError, "contamination"):
            validate_inputs(*values)

    def test_dhs_numbering_cannot_be_silently_repaired(self):
        values = copy.deepcopy(self.values)
        action = next(a for a in values[0]["actions"] if a["bill_number"] == 901)
        action["compact_description"] = "The bill adds a new paragraph (16)."
        with self.assertRaisesRegex(ValueError, "instruction qualification lost"):
            validate_inputs(*values)

    def test_resealed_pending_row_cannot_become_unavailable_evidence(self):
        values = copy.deepcopy(self.values)
        universe = values[2]
        universe["candidate_dispositions"][0]["review_progress"]["required_evidence_unavailable"] = True
        universe["universe_subject_sha256"] = digest(dict(subject=universe["subject"],
            cutoff=universe["cutoff"],candidate_records=universe["candidate_dispositions"]))
        universe["proposal_sha256"] = sealed_digest(universe, "proposal_sha256")
        with self.assertRaisesRegex(ValueError, "unfinished research misrepresented"):
            validate_inputs(*values)

    def test_exact_clerk_question_cannot_be_changed(self):
        author, capture, _, _ = copy.deepcopy(self.values)
        source = next(s for s in capture["sources"] if s["source_id"] == "clerk:119:1:74")
        source["metadata"]["vote-question"] = "On Agreeing to the Amendment"
        source["governed_bytes_sha256"] = sealed_digest(source, "governed_bytes_sha256")
        with self.assertRaisesRegex(ValueError, "stage differs"):
            prepare(author, capture, ["F000477", "M001184"])

    def test_approval_cannot_be_manufactured_by_resealing(self):
        values = copy.deepcopy(self.values)
        universe = values[2]
        universe["approval_receipt"] = {"approved": True}
        universe["proposal_sha256"] = sealed_digest(universe, "proposal_sha256")
        with self.assertRaisesRegex(ValueError, "cannot confer"):
            validate_inputs(*values)


if __name__ == "__main__":
    unittest.main()
