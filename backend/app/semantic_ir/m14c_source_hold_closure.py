"""Bounded M14C provenance and acceptance checks; no semantic-quality compiler."""

from __future__ import annotations

import copy
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import subprocess
from typing import Any

from backend.app.semantic_ir.action_interpretability import (
    canonical_bytes, digest, file_sha256, load_json,
    validate_candidate_set,
)

BASE = "f666b4a4c2c0c11c04e49d50cef9cc04ab7aaf83"
BASE_DIGEST = "7446ba60c7995e877026e26a6b18837550ccde52ba323c56c9b59decb914f4bd"
BASE_DIR = "docs/editorial/interpretability_candidates/house_119_v1/education_workforce_v1"
OUTPUT = "docs/editorial/interpretability_candidates/house_119_v1/education_workforce_m14c_v1"
ACCEPTED_IDS = (
    "house:119:1:120", "house:119:1:146", "house:119:1:312", "house:119:1:313",
    "house:119:1:314", "house:119:1:315", "house:119:1:68", "house:119:1:83",
    "house:119:2:19", "house:119:2:216", "house:119:2:217", "house:119:2:31",
    "house:119:2:47", "house:119:2:82",
)
HOLD_IDS = ("house:119:1:79", "house:119:1:332", "house:119:2:184")
AM = "govinfo:CREC-2025-03-25-pt1-PgH1241:amendment-3"
EO51 = "govinfo:FR-2025-04-03:2025-05836:EO14251"
EO68 = "govinfo:FR-2025-01-30:2025-02090:EO14168"
HEA = "govinfo:USCODE-2024-title20:sec1094:e2Bii"
# Exact official downloads and source-role scopes. End markers are exclusive.
SPECS = (
    {
        "source_id": AM, "action_id": "house:119:1:79",
        "source_type": "congressional_record", "content_class": "operative_amendment_text",
        "relation_role": "exact_amendment_operative_text",
        "source_url": "https://www.govinfo.gov/content/pkg/CREC-2025-03-25/html/CREC-2025-03-25-pt1-PgH1241.htm",
        "sha256": "eaafafb53de434c894f475a864a1cd951118a32f2f98e1e487109f7ef71f5b32",
        "scope_start": "Page 1, strike line 1 and all that follows through page 60,",
        "scope_end": "The Acting CHAIR. Pursuant",
        "anchor": "AMENDMENT NO. 3 OFFERED BY MR. SCOTT OF VIRGINIA",
        "locators": (
            ("H1255; substitute section 2, HEA117(a)-(b)", "``(a) Disclosure Reports.--", "``(c) Additional Disclosures"),
            ("H1255; HEA117(c)-(d)", "``(c) Additional Disclosures", "``(e) Relation to Other"),
            ("H1255; HEA117(e)-(f)", "``(e) Relation to Other", "``(g) Sanctions"),
            ("H1255; HEA117(g)", "``(g) Sanctions", "``(h) Compliance Officer"),
            ("H1255-H1256; HEA117(h)-(i)", "``(h) Compliance Officer", "``(j) Treatment"),
            ("H1256; HEA117(j)-(l)", "``(j) Treatment", "SEC. 3. REGULATIONS."),
            ("H1256; substitute section 3(a)-(c)", "SEC. 3. REGULATIONS.", None),
        ),
    },
    {
        "source_id": EO51, "action_id": "house:119:1:332",
        "source_type": "federal_register_executive_order", "content_class": "referenced_order_operative_text",
        "relation_role": "order_targeted_for_nullification",
        "source_url": "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm",
        "sha256": "4852df435166d6164bbc331d8218cc9ceeb9f3ecede99b987f4b671278254528",
        "anchor": "Executive Order 14251 of March 27, 2025",
        "scope_start": "Section 1. Determinations.", "scope_end": "(Presidential Sig.)",
        "locators": (
            ("90 FR 14553-14555; EO14251 sections 1-2, including 1-401 through 1-499", "Section 1. Determinations.", "Sec. 3. Foreign Service Exclusions."),
            ("90 FR 14555; EO14251 section 3", "Sec. 3. Foreign Service Exclusions.", "Sec. 4. Delegation"),
            ("90 FR 14555-14556; EO14251 sections 4-5", "Sec. 4. Delegation", "Sec. 6. Implementation."),
            ("90 FR 14556-14557; EO14251 sections 6-8", "Sec. 6. Implementation.", None),
        ),
    },
    {
        "source_id": EO68, "action_id": "house:119:2:184",
        "source_type": "federal_register_executive_order", "content_class": "incorporated_definition",
        "relation_role": "definition_incorporated_by_bill_section_3",
        "source_url": "https://www.govinfo.gov/content/pkg/FR-2025-01-30/html/2025-02090.htm",
        "sha256": "dff6c48ef10fd7c7587c04dcc97f6e3c674c99229e6e33f6574c62495b10e03c",
        "anchor": "Executive Order 14168 of January 20, 2025",
        "scope_start": "Sec. 2. Policy and Definitions.", "scope_end": "Sec. 3. Recognizing",
        "locators": (("90 FR 8615-8616; EO14168 section 2(a)-(g), especially 2(f)-(g)", "Sec. 2. Policy and Definitions.", None),),
    },
    {
        "source_id": HEA, "action_id": "house:119:1:79",
        "source_type": "united_states_code", "content_class": "incorporated_exception",
        "relation_role": "gift_exception_incorporated_by_amendment_117l4B",
        "source_url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/USCODE-2024-title20-chap28-subchapIV-partG-sec1094.htm",
        "sha256": "cdd8d42fff6c79e9693c43bc7f8b0c564b593938802d19b09012c267400d6b7f",
        "anchor": "(e) Code of conduct requirements",
        "scope_start": "(ii) Exceptions", "scope_end": "(iii) Rule for gifts",
        "locators": (("20 USC1094(e)(2)(B)(ii)(I)-(VI), 2024 edition; HEA487(e)(2)(B)(ii)", "(ii) Exceptions", None),),
    },
)


class ClosureError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureError(message)


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def source_catalog(root: Path) -> dict[str, Any]:
    sources = []
    for spec in SPECS:
        relative = f"{OUTPUT}/evidence/{spec['sha256']}.html"
        raw = (root / relative).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == spec["sha256"], f"official source bytes differ: {spec['source_id']}")
        parser = _Text()
        parser.feed(raw.decode("utf-8"))
        text = " ".join(" ".join(parser.parts).split())
        anchor = text.index(spec["anchor"])
        start = text.index(spec["scope_start"], anchor)
        end = text.index(spec["scope_end"], start)
        scope = text[start:end].strip()
        excerpts = []
        for locator, begin, finish in spec["locators"]:
            left = scope.index(begin)
            right = scope.index(finish, left) if finish else len(scope)
            excerpt = scope[left:right].strip()
            excerpts.append({"locator": locator, "text": excerpt, "text_sha256": hashlib.sha256(excerpt.encode()).hexdigest()})
        projection = {"schema_version": "m14c_official_source_excerpts_v1", "source_id": spec["source_id"], "excerpts": excerpts}
        sources.append({
            key: spec[key] for key in ("source_id", "action_id", "source_type", "content_class", "relation_role", "source_url")
        } | {"raw_provenance": {"governed_local_path": relative, "sha256": spec["sha256"]},
             "neutral_projection": projection, "neutral_projection_sha256": digest(projection)})
    return {"schema_version": "m14c_governed_source_catalog_v1", "sources": sources}


def baseline(root: Path) -> dict[str, Any]:
    artifact = load_json(root / BASE_DIR / "action_interpretability_candidates.json")
    require(digest(artifact["candidates"]) == BASE_DIGEST, "immutable M14B candidate set differs")
    return artifact


def expected_authority(root: Path) -> dict[str, Any]:
    artifact = baseline(root)
    manifest = load_json(root / BASE_DIR / "build_manifest.json")
    manifest_digests = {item["action_id"]: item["sha256"] for item in manifest["subject"]["candidate_record_digests"]}
    by_id = {row["action_id"]: row for row in artifact["candidates"]}
    records = []
    for action_id in ACCEPTED_IDS:
        record = by_id[action_id]
        require(digest(record) == manifest_digests[action_id], "baseline record/manifest mismatch")
        records.append({"action_id": action_id, "candidate_id": record["candidate_id"],
                        "candidate_record_sha256": manifest_digests[action_id], "decision": "accept_as_written"})
    subject = {
        "baseline_commit": BASE, "m14b_candidate_set_sha256": BASE_DIGEST,
        "candidate_path": f"{BASE_DIR}/action_interpretability_candidates.json",
        "manifest_path": f"{BASE_DIR}/build_manifest.json",
        "manifest_sha256": file_sha256(root / BASE_DIR / "build_manifest.json"),
        "human_decision_source": "user_supplied_M14C_milestone_request",
        "decision_date": "2026-08-27", "accepted_records": records,
        "explicitly_unaccepted_source_hold_ids": list(HOLD_IDS),
        "authorizations": {"later_canonical_semantic_promotion_of_exact_accepted_records": True,
                           "promotion_during_m14c": False, "public_wording": False,
                           "synthesis": False, "publication": False,
                           "production_persistence": False, "deployment": False},
        "historical_m13_authority_replaced": False,
    }
    return {"schema_version": "m14b_human_candidate_acceptance_authority_v1",
            "artifact_id": "human-action-interpretability-authority:house:119:m14b:accepted14:v1",
            "artifact_role": "immutable_human_candidate_acceptance_authority", "immutable": True,
            "subject": subject, "authority_subject_sha256": digest(subject)}


def source_overlay(root: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    base = baseline(root)
    old = load_json(root / base["input_bindings"]["source_readiness"]["path"])
    rows = copy.deepcopy(old["subject"]["action_readiness"])
    for row in rows:
        additions = [source for source in catalog["sources"] if source["action_id"] == row["action_id"]]
        if not additions:
            continue
        # Do not misrepresent the legacy source-readiness validator as accepting
        # new source types. This is a separate bounded overlay for V1 qualification.
        for key in ("readiness_criteria", "readiness_state", "blocker_codes", "material_limitations"):
            row.pop(key, None)
        row["baseline_source_packet_sha256"] = row.pop("source_packet_sha256")
        row["sources"].extend(additions)
        operative = row["source_roles"]["operative_content_interpretation_input"]
        if row["action_id"] == "house:119:1:79":
            operative.clear()  # Purpose-only index is no longer operative meaning.
        operative.extend(source["source_id"] for source in additions)
        row["source_packet_sha256"] = digest(row)
    subject = {"action_readiness": rows}
    return {"schema_version": "m14c_interpretability_source_overlay_v1",
            "artifact_id": "interpretability-source-overlay:house:119:education:m14c:v1",
            "artifact_role": "detached_non_authorizing_source_overlay",
            "baseline_source_readiness": base["input_bindings"]["source_readiness"],
            "subject": subject, "source_readiness_subject_sha256": digest(subject)}


def validate_scope(root: Path) -> None:
    allowed = {".github/workflows/backend-tests.yml",
               "backend/app/semantic_ir/m14c_source_hold_closure.py",
               "backend/tests/test_m14c_source_hold_closure.py",
               "scripts/build_m14c_source_hold_closure.py", "scripts/m14c_candidate_drafts.py"}
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE], cwd=root, text=True).splitlines()
    forbidden = [name for name in changed if name not in allowed and not name.startswith(OUTPUT + "/")]
    require(not forbidden, f"protected baseline artifact changed: {forbidden}")


def validate_closure(root: Path, artifact: dict[str, Any], authority: dict[str, Any],
                     catalog: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    require(authority == expected_authority(root), "immutable human authority differs from supplied exact14 decision")
    require(catalog == source_catalog(root), "source identity, excerpt, digest, or relation role differs")
    require(overlay == source_overlay(root, catalog), "source overlay differs from governed role-bound inputs")
    base = baseline(root)
    before = {row["action_id"]: row for row in base["candidates"]}
    current = {row["action_id"]: row for row in artifact["candidates"]}
    require(len(artifact["candidates"]) == 17 and set(current) == set(before), "candidate membership differs")
    for action_id in ACCEPTED_IDS:
        require(canonical_bytes(current[action_id]) == canonical_bytes(before[action_id]), f"accepted record changed: {action_id}")
    overlay_path = f"{OUTPUT}/source_overlay.json"
    expected = copy.deepcopy(base["input_bindings"])
    expected["starting_main"] = BASE
    expected["source_readiness"] = {"path": overlay_path, "sha256": file_sha256(root / overlay_path),
                                    "artifact_id": overlay["artifact_id"], "subject_sha256": overlay["source_readiness_subject_sha256"]}
    require(artifact["input_bindings"] == expected, "M14C input bindings differ")
    require(artifact["protected_historical_artifacts"] == base["protected_historical_artifacts"], "protected bindings differ")
    lookup = {s["source_id"]: s for s in catalog["sources"]}
    for action_id in HOLD_IDS:
        candidate = current[action_id]
        require(candidate["candidate_id"] == f"action-interpretability-candidate:{action_id}:m14c:v1", "enriched candidate identity differs")
        for key in ("action_id", "exact_action_identity", "legislative_stage", "action_date", "shared_action_core_reference", "current_accepted_legacy_meaning"):
            require(candidate[key] == before[action_id][key], f"exact action/legacy boundary changed: {action_id}:{key}")
        for mapping in candidate["claim_source_mappings"]:
            if mapping["source_id"] in lookup:
                source = lookup[mapping["source_id"]]
                require(source["action_id"] == action_id, "cross-action source role")
                require(mapping["locator"] in {e["locator"] for e in source["neutral_projection"]["excerpts"]}, "ungoverned source locator")
            else:
                # Only the two governed parent bills can supply their own operative
                # clauses. H.R.1048 never supplies this exact amendment's meaning.
                bill = {"house:119:1:332": "congress-text:119:hr:2550:eh", "house:119:2:184": "congress-text:119:hr:2616:eh"}.get(action_id)
                require(mapping["source_id"] == bill, "wrong operative source role")
                require(mapping["locator"] == before[action_id]["claim_source_mappings"][0]["locator"], "ungoverned bill locator")
        expected_new = {s["source_id"] for s in catalog["sources"] if s["action_id"] == action_id}
        require(expected_new <= {m["source_id"] for m in candidate["claim_source_mappings"]}, "new source not claim-bound")
    result = validate_candidate_set(root, artifact)
    return result | {"human_accepted_unchanged_count": 14, "newly_accepted_count": 0,
                     "remaining_source_hold_ids": [r["action_id"] for r in artifact["candidates"] if r["candidate_state"] != "candidate_complete_for_semantic_review"]}
