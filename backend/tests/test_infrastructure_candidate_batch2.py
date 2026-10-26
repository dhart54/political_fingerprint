"""Batch2 evidence, nondirectional input and protected-boundary regressions."""
import copy
import unittest
from scripts.validate_infrastructure_candidate_batch2 import DATA, read, validate, versions
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest


class InfrastructureBatch2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values=[read(DATA/f"{n}.json") for n in ["authoring","sources","universe_proposal","membership_review"]]

    def test_replay_accepts_real_nondirectional_authoring(self):
        r=validate(*self.values)
        self.assertEqual(r["not_voting_counts"],{"F000477":1,"M001184":3})
        self.assertEqual(r["finding_counts"],{"F000477":8,"M001184":6})

    def test_matching_resealed_directional_label_cannot_override_not_voting(self):
        values=copy.deepcopy(self.values);u,m=values[2:]
        row=next(r for r in u["candidate_dispositions"] if r["action_id"]=="house:119:1:157")
        rec=next(r for r in m["records"] if r["action_id"]==row["action_id"])
        row["disposition"]=rec["disposition"]="interpreted_substantive_directional"
        other=next(r for r in u["candidate_dispositions"] if r["action_id"]=="house:119:1:191")
        other_rec=next(r for r in m["records"] if r["action_id"]==other["action_id"])
        other["disposition"]=other_rec["disposition"]="interpreted_substantive_non_directional"
        m["review_sha256"]=sealed_digest(m,"review_sha256");u["membership_review_sha256"]=m["review_sha256"]
        row["review_progress"]["shared_review_record_sha256"]=digest(rec)
        other["review_progress"]["shared_review_record_sha256"]=digest(other_rec)
        u["accounting"]["action_ids_by_disposition"]={
            kind:[r["action_id"] for r in u["candidate_dispositions"] if r["disposition"]==kind]
            for kind in u["accounting"]["counts"]}
        u["universe_subject_sha256"]=digest(dict(subject=u["subject"],cutoff=u["cutoff"],candidate_records=u["candidate_dispositions"]))
        u["proposal_sha256"]=sealed_digest(u,"proposal_sha256")
        with self.assertRaisesRegex(ValueError,"nondirectional disposition"):
            validate(*values,check_files=False)

    def test_coherently_resealed_floor_body_change_is_rejected(self):
        sources={s["source_id"]:copy.deepcopy(s) for s in self.values[1]["sources"]}
        s=sources["record:2025-06-09-hr2035-infra2"]
        for page in s["page_extracts"]:page["text"]=page["text"].replace("100 percent","75 percent")
        s["governed_bytes_sha256"]=sealed_digest(s,"governed_bytes_sha256")
        with self.assertRaisesRegex(ValueError,"floor body differs"):
            versions(sources)

    def test_new_compact_cannot_drop_material_duration_baseline(self):
        values=copy.deepcopy(self.values)
        action=next(a for a in values[0]["actions"] if a["bill_number"]==1717)
        action["compact_source_refs"].remove("govinfo:5usc1013-2024-operative")
        with self.assertRaisesRegex(ValueError,"compact lost material baseline"):
            validate(*values,check_files=False)

    def test_new_core_cannot_repeat_health_membership_conclusions(self):
        values=copy.deepcopy(self.values)
        action=next(a for a in values[0]["actions"] if a["bill_number"]==146)
        # A source quotation may discuss medical care. Membership conclusions
        # belong in mappings/review, not in the issue-neutral action core.
        action["meaning"] += " Proposed Health membership is established."
        # Enforce the candidate's explicit issue-neutral successor boundary.
        self.assertNotIn("Proposed Health membership",next(a for a in self.values[0]["actions"] if a["bill_number"]==146)["meaning"])
        with self.assertRaisesRegex(ValueError,"issue-specific membership"):
            validate(*values,check_files=False)

    def test_request_access_page_cannot_be_promoted_as_an_unused_source(self):
        values=copy.deepcopy(self.values)
        source=copy.deepcopy(values[1]["sources"][0])
        source.update(source_id="synthetic:denied",url="https://unblock.federalregister.gov/",
                      text="Federal Register :: Request Access")
        source["governed_bytes_sha256"]=sealed_digest(source,"governed_bytes_sha256")
        values[1]["sources"].append(source)
        with self.assertRaisesRegex(ValueError,"denied/error response promoted"):
            validate(*values,check_files=False)


if __name__=="__main__":unittest.main()
