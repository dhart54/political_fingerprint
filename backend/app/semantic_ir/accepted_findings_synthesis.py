"""Detached mechanism-divide review over pinned human-accepted M14D findings.

No legacy authority adapters, raw-action authoring input, or acceptance path.
Source pins are supplied by the milestone, never by candidate prose. Mechanical
checks establish lineage and review completeness, not semantic acceptance.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import re

from backend.app.semantic_ir.shared_corpus import digest


DENIED = {key: False for key in (
    "synthesis_acceptance", "main_takeaway", "public_wording", "frontend_changes",
    "publication", "production_persistence", "database_writes", "deployment", "merge",
)}
PROHIBITED_INFERENCES = [
    "A general preference for disclosure over enforcement.",
    "General opposition to funding conditions.",
    "General support for or opposition to foreign-influence regulation.",
    "A general position on China.",
    "Opposition to any particular component of final H.R.1048.",
    "Motive, ideology, character, corruption, partisan rationale, or a voting recommendation.",
    "A durable regulatory preference beyond the reviewed actions.",
    "Treating the substitute as merely soft disclosure without fines, compliance, exclusions, or rulemaking.",
]
MECHANISMS = {"funding_eligibility_restriction", "reporting_and_compliance"}
# Defense in depth, not a claim to infer truth or intent from arbitrary prose.
UNSAFE_CLAIM = re.compile(
    r"\b(motivated|motives?|ideolog\w*|partisan|corrupt\w*|pacifis\w*|isolationis\w*)\b"
    r"|party loyalty|because (?:she|he) (?:believes|wants)|vote for|vote against"
    r"|generally prefers|generally opposes|generally supports|soft disclosure",
    re.IGNORECASE,
)


class DetachedSynthesisError(ValueError):
    """A detached review artifact crossed its accepted-input boundary."""


@dataclass(frozen=True)
class AcceptedSourceBinding:
    findings_path: str
    findings_document_sha256: str
    authority_path: str
    authority_document_sha256: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DetachedSynthesisError(message)


def keys(value: dict, expected: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == expected, f"{label}: unexpected or missing fields")


def claim_text(value: str, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{label}: nonempty text required")
    require(not UNSAFE_CLAIM.search(value), f"{label}: prohibited claim language")


def accepted_records(findings: dict, authority: dict, binding: AcceptedSourceBinding) -> dict[str, dict]:
    """Verify full documents, their seals, and every record/ledger cross-binding."""
    require(digest(findings) == binding.findings_document_sha256, "accepted-findings document differs from trusted pin")
    require(digest(authority) == binding.authority_document_sha256, "human authority document differs from trusted pin")
    require(findings.get("schema_version") == "m14d_accepted_behavioral_findings_v1", "unsupported accepted findings")
    require(authority.get("schema_version") == "m14d_human_behavioral_candidate_authority_v1", "unsupported human authority")
    require(findings.get("internal_analytical_authority") is True and findings.get("public") is False
            and findings.get("production_selectable") is False, "findings must be accepted internally only")
    require(authority.get("immutable") is True, "human authority must be immutable")
    fs, hs = findings["subject"], authority["subject"]
    require(digest(fs) == findings["findings_subject_sha256"], "findings subject seal differs")
    require(digest(hs) == authority["authority_subject_sha256"], "authority subject seal differs")
    require(hs["authority_scope"] == "internal_analytical_findings_only", "wrong authority scope")
    require(fs["human_authority"] == {
        "path": binding.authority_path, "artifact_id": authority["artifact_id"],
        "authority_subject_sha256": authority["authority_subject_sha256"],
    }, "accepted findings bind a different human authority")
    require(fs["candidate_graph_sha256"] == hs["final_candidate_graph"]["content_sha256"], "graph binding differs")
    require(fs["accepted_episode_disposition_ledger"] == hs["accepted_episode_disposition_ledger"], "episode ledger differs")
    ledger = fs["accepted_episode_disposition_ledger"]
    require(digest(ledger) == hs["episode_disposition_ledger_sha256"], "ledger seal differs")
    require(digest(fs["relationship_evidence_by_proposition"]) == hs["relationship_evidence_sha256"], "relationship binding differs")
    require(fs["synthesis_propositions"] == [], "source findings cannot confer synthesis")
    for subject in (fs, hs):
        require(bool(subject["downstream_authorizations"]) and
                all(v is False for v in subject["downstream_authorizations"].values()), "source downstream authority escaped")
    rows = fs["accepted_proposition_records"]
    records = {r["proposition_id"]: r for r in rows}
    decisions = {r["proposition_id"]: r for r in hs["decisions"]}
    episodes = {r["episode_id"]: r for r in ledger}
    require(len(episodes) == len(ledger), "duplicate ledger episode")
    require(len(records) == len(rows) and len(decisions) == len(hs["decisions"])
            and set(records) == set(decisions), "accepted decision membership differs")
    for pid, record in records.items():
        require(decisions[pid]["decision"] in {"accepted_as_written", "accepted_after_exact_bounded_revision"}
                and decisions[pid]["accepted_record_sha256"] == digest(record), "record lacks exact human acceptance")
        # Candidate flags are retained provenance, never used to deny or infer acceptance.
        eids, aids = record["evidence_episode_ids"], record["evidence_action_ids"]
        require(len(eids) == len(set(eids)) and len(aids) == len(set(aids)), "duplicate source lineage")
        require(set(record["episode_semantic_evidence"]) == set(eids) and set(eids) <= set(episodes), "source episode lineage differs")
        require(set(aids) == {a for eid in eids for a in episodes[eid]["action_ids"]}, "source action lineage differs")
        require(all(episodes[eid]["primary_proposition_id"] == pid for eid in eids), "source ledger ownership differs")
    return records


def compile_detached_synthesis(
    findings: dict, authority: dict, binding: AcceptedSourceBinding,
    proposals: list[dict], standalone_reasons: dict[str, str],
) -> dict:
    """Compile zero or one candidate; all action/episode evidence is derived."""
    records = accepted_records(findings, authority, binding)
    require(isinstance(proposals, list) and len(proposals) <= 1, "this review supports zero or one hypothesis")
    require(isinstance(standalone_reasons, dict), "standalone accounting required")
    candidates, used, limiting = [], set(), set()
    for proposal in proposals:
        keys(proposal, {"proposition_id", "proposition_type", "summary", "source_finding_ids",
                        "relationship_evidence", "material_limiter_finding_ids", "competing_interpretation"}, "proposal")
        require(proposal["proposition_type"] == "mechanism_divide", "only mechanism_divide is supported")
        require(isinstance(proposal["proposition_id"], str) and bool(proposal["proposition_id"]), "candidate ID required")
        ids = proposal["source_finding_ids"]
        require(isinstance(ids, list) and len(ids) >= 2 and len(ids) == len(set(ids)), "at least two distinct accepted findings required")
        require(set(ids) <= set(records), "raw actions or unknown findings cannot be synthesis inputs")
        claim_text(proposal["summary"], "summary")
        claim_text(proposal["competing_interpretation"], "competing interpretation")
        rel = proposal["relationship_evidence"]
        keys(rel, {"basis", "claim_scope", "contrast", "mechanisms_by_finding"}, "relationship")
        require(rel["basis"] == "contrasting_policy_mechanisms", "topic-only relationships do not qualify")
        require(rel["claim_scope"] == "observed_reviewed_actions_only", "unbounded relationship claim")
        claim_text(rel["contrast"], "mechanism contrast")
        mechanisms = rel["mechanisms_by_finding"]
        require(isinstance(mechanisms, dict) and set(mechanisms) == set(ids), "mechanism evidence must cover each input finding")
        codes = set()
        for pid, evidence in mechanisms.items():
            keys(evidence, {"mechanism", "source_quote"}, "mechanism evidence")
            require(evidence["mechanism"] in MECHANISMS, "unsupported mechanism")
            source = records[pid]
            require(evidence["source_quote"] in [source["summary"], *source["episode_semantic_evidence"].values()],
                    "mechanism evidence must quote its accepted finding exactly")
            codes.add(evidence["mechanism"])
        require(len(codes) >= 2, "distinct mechanisms required, not a topic grouping")
        limiter_ids = proposal["material_limiter_finding_ids"]
        require(isinstance(limiter_ids, list) and len(limiter_ids) == len(set(limiter_ids))
                and set(limiter_ids) <= set(ids), "limiter must be an accepted synthesis input")
        require({pid for pid in ids if records[pid]["direction"] == "mixed"} <= set(limiter_ids),
                "mixed finding must remain a material limiter")
        limiting.update(limiter_ids)
        used.update(ids)
        lineage = [{"source_finding_id": pid, "accepted_record_sha256": digest(records[pid]),
                    "episode_ids": deepcopy(records[pid]["evidence_episode_ids"]),
                    "action_ids": deepcopy(records[pid]["evidence_action_ids"])} for pid in ids]
        episode_ids = sorted({e for row in lineage for e in row["episode_ids"]})
        action_ids = sorted({a for row in lineage for a in row["action_ids"]})
        candidate = deepcopy(proposal) | {
            "semantic_role": "synthesis", "candidate_state": "proposed_not_accepted",
            "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
            "independent_semantic_review_required": True,
            "source_lineage": lineage, "evidence_episode_ids": episode_ids, "evidence_action_ids": action_ids,
            "evidence_counts": {"accepted_findings": len(ids), "episodes": len(episode_ids), "actions": len(action_ids)},
            "inherited_material_limitations": {pid: deepcopy(records[pid]["material_limitations"]) for pid in ids},
            "inherited_episode_semantic_evidence": {pid: deepcopy(records[pid]["episode_semantic_evidence"]) for pid in ids},
            "prohibited_inferences": PROHIBITED_INFERENCES.copy(), "downstream_authorizations": DENIED.copy(),
        }
        candidates.append(candidate | {"candidate_sha256": digest(candidate)})
    require(set(standalone_reasons) == set(records) - used, "every unused accepted finding needs standalone accounting")
    for reason in standalone_reasons.values():
        claim_text(reason, "standalone reason")
    accounting = [{"source_finding_id": pid, "accepted_record_sha256": digest(record),
                   "disposition": "primary_synthesis_input" if pid in used else "intentionally_standalone_no_safe_synthesis",
                   "material_limiter": pid in limiting,
                   "candidate_ids": [c["proposition_id"] for c in candidates if pid in c["source_finding_ids"]],
                   "reason": ("Primary input to the proposed mechanism contrast; its full accepted record and limitations remain intact."
                              if pid in used else standalone_reasons[pid])}
                  for pid, record in records.items()]
    subject = {
        "accepted_source_binding": asdict(binding) | {
            "findings_subject_sha256": findings["findings_subject_sha256"],
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        "accepted_source_findings": deepcopy(list(records.values())),
        "source_finding_accounting": accounting,
        "inherited_episode_disposition_ledger": deepcopy(findings["subject"]["accepted_episode_disposition_ledger"]),
        "synthesis_candidates": candidates, "accepted_synthesis_count": 0,
        "downstream_authorizations": DENIED.copy(),
        "validation_boundary": "Exact accepted input binding, lineage and review completeness only; semantic usefulness requires independent human/product review.",
    }
    package = {"schema_version": "accepted_findings_synthesis_candidate_v1",
               "artifact_role": "detached_non_authorizing_synthesis_review",
               "accepted": False, "authorizing": False, "public": False, "production_selectable": False,
               "subject": subject}
    return package | {"package_sha256": digest(package)}


def validate_detached_synthesis(package: dict, findings: dict, authority: dict,
                                binding: AcceptedSourceBinding, proposals: list[dict],
                                standalone_reasons: dict[str, str]) -> None:
    require(package == compile_detached_synthesis(findings, authority, binding, proposals, standalone_reasons),
            "detached synthesis package differs from exact compilation")
