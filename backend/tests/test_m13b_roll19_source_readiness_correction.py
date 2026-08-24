from __future__ import annotations

from copy import deepcopy
import unittest

from pypdf import PdfReader, PdfWriter

from backend.app.etl.full_record_source_readiness import (
    load_json,
    sha256_file,
    sha256_json,
    verify_operative_floor_text_pdf,
)
from backend.scripts.build_m13b_education_workforce_source_readiness_v2 import (
    ACTION_ID,
    NEW_SOURCE_ID,
    V1_PATH,
    V2_PATH,
)
from scripts.validate_m13b_education_workforce_source_readiness_v2 import (
    old_source_rejection_state,
    operative_source,
    roll19_record,
)


class M13BRoll19SourceReadinessCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v1 = load_json(V1_PATH)
        cls.v2 = load_json(V2_PATH)
        cls.record = roll19_record(cls.v2)
        cls.root = V2_PATH.parents[4]
        cls.temp_root = cls.root / (
            "docs/editorial/full_record_reviews/source_readiness/evidence/"
            "_m13b_v2_pdf_tests"
        )
        cls.temp_root.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        for path in cls.temp_root.iterdir():
            path.unlink()
        cls.temp_root.rmdir()

    def _source_with_blank_pages(
        self, *, blank_pages: set[int], filename: str
    ) -> dict[str, object]:
        record = deepcopy(self.record)
        source = operative_source(record)
        original = self.root / source["raw_provenance"]["governed_local_path"]
        reader = PdfReader(original)
        writer = PdfWriter()
        for page_number, page in enumerate(reader.pages, start=1):
            if page_number in blank_pages:
                writer.add_blank_page(
                    width=float(page.mediabox.width),
                    height=float(page.mediabox.height),
                )
            else:
                writer.add_page(page)
        path = self.temp_root / filename
        with path.open("wb") as stream:
            writer.write(stream)
        digest = sha256_file(path)
        source["raw_provenance"] = {
            "governed_local_path": path.relative_to(self.root).as_posix(),
            "sha256": digest,
        }
        source["neutral_projection"]["raw_provenance_sha256"] = digest
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        return source

    def test_complete_house_section_satisfies_all_declared_anchors(self) -> None:
        source = operative_source(self.record)
        self.assertTrue(
            verify_operative_floor_text_pdf(source, repository_root=V2_PATH.parents[4])
        )

    def test_defective_two_page_pdf_is_rejected(self) -> None:
        self.assertNotEqual(
            old_source_rejection_state(self.record),
            "ready_for_action_interpretation",
        )

    def test_missing_h678_operative_completion_fails_contract(self) -> None:
        source = self._source_with_blank_pages(
            blank_pages={16}, filename="missing-h678.pdf"
        )
        self.assertFalse(
            verify_operative_floor_text_pdf(source, repository_root=self.root)
        )

    def test_missing_h692_h693_final_vote_linkage_fails_contract(self) -> None:
        source = self._source_with_blank_pages(
            blank_pages={30, 31}, filename="missing-h692-h693.pdf"
        )
        self.assertFalse(
            verify_operative_floor_text_pdf(source, repository_root=self.root)
        )

    def test_roll19_stage_member_action_and_no_substitute_are_exact(self) -> None:
        self.assertEqual(self.record["action_id"], ACTION_ID)
        self.assertEqual(
            self.record["house_action_stage"],
            "final_passage_or_suspension_passage",
        )
        self.assertEqual(self.record["official_member_action"], "nay")
        self.assertEqual(
            self.record["source_roles"]["operative_content_interpretation_input"],
            [NEW_SOURCE_ID],
        )
        self.assertFalse(
            any(
                source["content_class"] == "operative_measure_text"
                for source in self.record["sources"]
            )
        )

    def test_other_sixteen_source_packets_are_byte_semantic_identical(self) -> None:
        v1_by_id = {
            row["action_id"]: row
            for row in self.v1["subject"]["action_readiness"]
            if row["action_id"] != ACTION_ID
        }
        v2_by_id = {
            row["action_id"]: row
            for row in self.v2["subject"]["action_readiness"]
            if row["action_id"] != ACTION_ID
        }
        self.assertEqual(v1_by_id, v2_by_id)


if __name__ == "__main__":
    unittest.main()
