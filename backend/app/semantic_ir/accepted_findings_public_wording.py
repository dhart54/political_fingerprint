"""Detached public-wording review over pinned current-path accepted semantics."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import re

from backend.app.semantic_ir.accepted_findings_synthesis import (
    AcceptedSourceBinding, DetachedSynthesisError, accepted_records,
)
from backend.app.semantic_ir.shared_corpus import digest


DENIED = {key: False for key in (
    "public_wording_acceptance", "main_takeaway_prominence_acceptance",
    "canonical_public_copy", "frontend_changes", "site_integration", "publication",
    "production_persistence", "database_writes", "production_writes", "deployment", "merge",
)}
TREATMENTS = {"retained_public_copy", "compressed_or_omitted"}
BEHAVIORAL_SURFACES = {"repeated_pattern": "repeated_pattern", "notable_choice": "notable_choice"}
UNSAFE_LANGUAGE = re.compile(
    r"institutional relationships or support|section 117|relationship/support|\bframework\b"
    r"|\b(motive|motivated|ideolog\w*|partisan|corrupt\w*|betray\w*|extrem\w*)\b"
    r"|\b(democrat|republican|pro[- ]?labor|anti[- ]?china)\b|\b(always|never|consistently|typically)\b"
    r"|\b(good|bad) (?:bill|policy|vote)|\bvoters? (?:should|must)\b|became law"
    r"|generally (?:prefers|supports|opposes)"
    r"|(?:opposes|opposition to) (?:china policy|foreign-influence regulation|education funding conditions|disclosure requirements)",
    re.IGNORECASE,
)


class PublicWordingReviewError(ValueError):
    """A wording candidate escaped accepted semantics or review-only state."""


@dataclass(frozen=True)
class PublicWordingSourceBinding:
    findings_path: str
    findings_document_sha256: str
    behavioral_authority_path: str
    behavioral_authority_document_sha256: str
    synthesis_path: str
    synthesis_document_sha256: str
    synthesis_authority_path: str
    synthesis_authority_document_sha256: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicWordingReviewError(message)


def keys(value: dict, expected: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == expected, f"{label}: unexpected or missing fields")


def safe_public_text(value: str, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{label}: nonempty text required")
    require(not UNSAFE_LANGUAGE.search(value), f"{label}: prohibited public language")


def accepted_semantics(findings: dict, behavioral_authority: dict, accepted_synthesis: dict,
                       synthesis_authority: dict, binding: PublicWordingSourceBinding) -> tuple[dict, dict]:
    """Verify the four pinned documents and their full current-path cross-bindings."""
    require(digest(findings) == binding.findings_document_sha256, "M14D accepted findings differ from trusted pin")
    require(digest(behavioral_authority) == binding.behavioral_authority_document_sha256,
            "M14D human authority differs from trusted pin")
    require(digest(accepted_synthesis) == binding.synthesis_document_sha256,
            "M14E accepted synthesis differs from trusted pin")
    require(digest(synthesis_authority) == binding.synthesis_authority_document_sha256,
            "M14E human authority differs from trusted pin")
    try:
        records = accepted_records(findings, behavioral_authority, AcceptedSourceBinding(
            binding.findings_path, binding.findings_document_sha256,
            binding.behavioral_authority_path, binding.behavioral_authority_document_sha256))
    except DetachedSynthesisError as error:
        raise PublicWordingReviewError(str(error)) from error
    require(len(records) == 3, "exactly three accepted behavioral findings required")
    require(accepted_synthesis.get("accepted") is True
            and accepted_synthesis.get("canonical_internal_synthesis") is True
            and accepted_synthesis.get("public") is False
            and accepted_synthesis.get("production_selectable") is False,
            "M14E input must be accepted internal synthesis only")
    require(synthesis_authority.get("immutable") is True, "M14E authority must be immutable")
    ss, hs = accepted_synthesis["subject"], synthesis_authority["subject"]
    require(digest(ss) == accepted_synthesis["accepted_internal_synthesis_subject_sha256"],
            "M14E accepted synthesis seal differs")
    require(digest(hs) == synthesis_authority["authority_subject_sha256"], "M14E authority seal differs")
    require(hs["decision"] == "accept_as_written" and hs["authority_effect"] == "canonical_internal_synthesis_only",
            "M14E authority effect differs")
    require(ss["human_synthesis_authority"] == {
        "path": binding.synthesis_authority_path, "artifact_id": synthesis_authority["artifact_id"],
        "authority_subject_sha256": synthesis_authority["authority_subject_sha256"],
    }, "M14E accepted synthesis binds another authority")
    synthesis_rows = ss["accepted_synthesis_records"]
    require(ss["accepted_synthesis_count"] == 1 and len(synthesis_rows) == 1,
            "exactly one accepted internal synthesis required")
    synthesis = synthesis_rows[0]
    require(synthesis["candidate_sha256"] == ss["candidate_sha256"] == hs["candidate_sha256"]
            and synthesis["proposition_id"] == hs["candidate_id"], "M14E candidate identity differs")
    require(digest({k: v for k, v in synthesis.items() if k != "candidate_sha256"}) == synthesis["candidate_sha256"],
            "M14E candidate content digest differs")
    require([r["proposition_id"] for r in ss["accepted_input_findings"]] == synthesis["source_finding_ids"]
            and ss["accepted_input_findings"] == [records[pid] for pid in synthesis["source_finding_ids"]],
            "M14E synthesis inputs differ from accepted behavioral records")
    standalone = ss["intentionally_standalone_finding"]
    require(standalone["finding"] == records[standalone["finding"]["proposition_id"]]
            and standalone["accounting"]["disposition"] == "intentionally_standalone_no_safe_synthesis"
            and standalone["accounting"]["candidate_ids"] == [], "standalone finding escaped")
    require(ss["source_finding_accounting"] == hs["source_finding_accounting"], "M14E finding accounting differs")
    require(ss["inherited_episode_disposition_ledger"] == findings["subject"]["accepted_episode_disposition_ledger"],
            "M14E inherited ledger differs from M14D")
    require(ss["source_lineage"] == synthesis["source_lineage"]
            and ss["evidence_counts"] == synthesis["evidence_counts"] == {
                "accepted_findings": 2, "episodes": 3, "actions": 4}, "M14E synthesis lineage differs")
    require(ss["inherited_material_limitations"] == synthesis["inherited_material_limitations"],
            "M14E limitations differ")
    for subject in (findings["subject"], behavioral_authority["subject"], ss, hs):
        require(all(v is False for v in subject["downstream_authorizations"].values()),
                "source downstream authority escaped")
    return records, synthesis


def limitations(source_id: str, source: dict, source_kind: str) -> list[dict]:
    if source_kind == "behavioral":
        return [{"limitation_id": f"{source_id}:material_limitations:{i}", "text": text}
                for i, text in enumerate(source["material_limitations"])]
    result = []
    for finding_id in source["source_finding_ids"]:
        result.extend({"limitation_id": f"{source_id}:inherited:{finding_id}:{i}", "text": text}
                      for i, text in enumerate(source["inherited_material_limitations"][finding_id]))
    return result


def compile_public_wording(findings: dict, behavioral_authority: dict, accepted_synthesis: dict,
                           synthesis_authority: dict, binding: PublicWordingSourceBinding,
                           definitions: list[dict], prominence_review: dict) -> dict:
    records, synthesis = accepted_semantics(
        findings, behavioral_authority, accepted_synthesis, synthesis_authority, binding)
    require(isinstance(definitions, list) and len(definitions) in {3, 4},
            "exactly three behavioral items and zero or one overview required")
    items, seen, behavioral_used, synthesis_used = [], set(), set(), set()
    for definition in definitions:
        keys(definition, {"wording_item_id", "surface", "public_title", "evidence_count_label",
                          "direction_display", "primary_sentence", "semantic_source_id",
                          "limitation_treatments"}, "wording definition")
        item_id, source_id = definition["wording_item_id"], definition["semantic_source_id"]
        require(isinstance(item_id, str) and item_id not in seen, "duplicate or missing wording item ID")
        seen.add(item_id)
        for field in ("public_title", "evidence_count_label", "primary_sentence"):
            safe_public_text(definition[field], f"{item_id}.{field}")
        if source_id in records:
            source, source_kind = records[source_id], "behavioral"
            require(definition["surface"] == BEHAVIORAL_SURFACES.get(source["proposition_type"]),
                    "behavioral surface differs from accepted semantic type")
            require(source_id not in behavioral_used, "behavioral finding has multiple primary wording items")
            behavioral_used.add(source_id)
            require(definition["direction_display"] == ({"label": "Mixed", "symbol": "±"}
                    if source["direction"] == "mixed" else None), "behavioral direction display differs")
            source_sha = digest(source)
            lineage = {"accepted_findings": 1, "episode_ids": deepcopy(source["evidence_episode_ids"]),
                       "action_ids": deepcopy(source["evidence_action_ids"])}
            extra_boundaries = None
        else:
            require(source_id == synthesis["proposition_id"], "unknown or topic-only semantic source")
            source, source_kind = synthesis, "accepted_internal_synthesis"
            require(definition["surface"] == "issue_overview" and definition["direction_display"] is None,
                    "accepted synthesis may only source a directionless issue overview")
            require(source_id not in synthesis_used, "accepted synthesis has multiple overview items")
            synthesis_used.add(source_id)
            source_sha = source["candidate_sha256"]
            lineage = {"accepted_findings": source["evidence_counts"]["accepted_findings"],
                       "episode_ids": deepcopy(source["evidence_episode_ids"]),
                       "action_ids": deepcopy(source["evidence_action_ids"])}
            ss = accepted_synthesis["subject"]
            extra_boundaries = {"competing_interpretation": ss["competing_interpretation"],
                                "prohibited_inferences": deepcopy(ss["prohibited_inferences"]),
                                "substantive_boundary": ss["substantive_boundary"],
                                "hr1048_final_passage_limitation": ss["hr1048_final_passage_limitation"]}
        source_limits = limitations(source_id, source, source_kind)
        treatments = definition["limitation_treatments"]
        require(isinstance(treatments, list) and len(treatments) == len(source_limits),
                "every source limitation requires exactly one treatment")
        for treatment in treatments:
            keys(treatment, {"limitation_id", "treatment", "reason"}, "limitation treatment")
        indexed = {r["limitation_id"]: r for r in treatments}
        require(len(indexed) == len(treatments) and set(indexed) == {r["limitation_id"] for r in source_limits},
                "limitation treatment coverage differs")
        rendered = []
        for source_limit in source_limits:
            treatment = indexed[source_limit["limitation_id"]]
            require(treatment["treatment"] in TREATMENTS, "unsupported limitation treatment")
            if treatment["treatment"] == "retained_public_copy":
                require(treatment["reason"] is None, "retained limitation cannot carry omission reason")
            else:
                require(isinstance(treatment["reason"], str) and len(treatment["reason"].strip()) >= 30
                        and "too complicated" not in treatment["reason"].lower(),
                        "compressed limitation needs a concrete reason")
            rendered.append(source_limit | deepcopy(treatment))
        item = {k: deepcopy(v) for k, v in definition.items() if k != "limitation_treatments"} | {
            "semantic_source": {"source_kind": source_kind, "source_id": source_id,
                                "accepted_record_sha256": source_sha},
            "derived_lineage": lineage, "limitation_treatments": rendered,
            "additional_semantic_boundaries": extra_boundaries,
            "candidate_state": "proposed_not_accepted", "accepted": False, "authorizing": False,
            "public": False, "production_selectable": False, "downstream_authorizations": DENIED.copy(),
        }
        items.append(item | {"wording_item_sha256": digest(item)})
    require(behavioral_used == set(records), "every behavioral finding needs exactly one primary wording item")
    require(len(synthesis_used) <= 1, "at most one Main Takeaway candidate is supported")
    keys(prominence_review, {"semantic_validity", "decision_state", "option_a_main_takeaway",
                             "option_b_no_main_takeaway", "proposed_prominence_note",
                             "main_takeaway_alternative"}, "prominence review")
    require(prominence_review["semantic_validity"] == "accepted_internal_synthesis_not_reopened"
            and prominence_review["decision_state"] == "pending_independent_human_product_review",
            "semantic validity and public prominence must remain separate")
    require(prominence_review["main_takeaway_alternative"] == "omit_main_takeaway_and_retain_all_three_findings",
            "zero-Main-Takeaway alternative missing")
    safe_public_text(prominence_review["proposed_prominence_note"], "prominence note")
    for option in (prominence_review["option_a_main_takeaway"], prominence_review["option_b_no_main_takeaway"]):
        require(isinstance(option, list) and option and all(isinstance(v, str) and v.strip() for v in option),
                "prominence option needs explicit review considerations")
        for consideration in option:
            safe_public_text(consideration, "prominence consideration")
    subject = {
        "selected_issue_experience_version": "v1.1", "accepted_source_binding": asdict(binding),
        "wording_items": items,
        "behavioral_finding_accounting": [{"source_finding_id": pid,
                                            "wording_item_id": next(i["wording_item_id"] for i in items if i["semantic_source_id"] == pid)}
                                           for pid in records],
        "synthesis_accounting": {"source_synthesis_id": synthesis["proposition_id"],
                                 "disposition": "proposed_issue_overview" if synthesis_used else "accepted_semantics_retained_no_overview_wording",
                                 "wording_item_ids": [i["wording_item_id"] for i in items if i["semantic_source_id"] == synthesis["proposition_id"]]},
        "prominence_review": deepcopy(prominence_review),
        "excluded_non_directional_receipts": [deepcopy(r) for r in findings["subject"]["accepted_episode_disposition_ledger"]
                                               if r["disposition"] == "non_directional_receipt"],
        "downstream_authorizations": DENIED.copy(),
    }
    package = {"schema_version": "m14f_public_wording_candidate_v1",
               "artifact_role": "detached_non_authorizing_public_wording_and_prominence_review",
               "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
               "subject": subject}
    return package | {"package_sha256": digest(package)}


def validate_public_wording(package: dict, *args) -> None:
    require(package == compile_public_wording(*args), "public wording package differs from exact compilation")
