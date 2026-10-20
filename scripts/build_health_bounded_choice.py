"""Build/check detached Health candidates. Never invent an owner decision."""

from __future__ import annotations

import argparse
import json

from backend.app.editorial_presentations import bounded_choice_review as review
from scripts.validate_full_record_issue_interpretation import validate_review

OUTPUT = review.ROOT / "docs/editorial/review_packages/health_bounded_choice_v1"


def products() -> dict[str, dict]:
    from backend.app.editorial_presentations import bounded_choice_pair as pair

    foundation = review.load_foundation()
    review.source_evidence()
    bundles = {}
    for member in review.MEMBERS:
        subject = review.build_semantic_subject(foundation, member)
        validate_review(subject["accounting_review"], authority_root=review.ROOT)
        presentation = review.build_presentation(subject, foundation)
        rendering = json.loads(
            (OUTPUT / f"{member.lower()}-rendering.json").read_text(encoding="utf-8")
        )
        bundles[member] = {
            "semantic": subject,
            "accounting": subject["accounting_review"],
            "presentation": presentation,
            "rendering": rendering,
        }
    shared = pair.build_pair_subject(bundles)
    result = {"pair-subject.json": shared}
    for member, b in bundles.items():
        for suffix in ["semantic", "accounting", "presentation"]:
            result[f"{member.lower()}-{suffix}.json"] = b[suffix]
        receipt = review.pending_receipt(
            b["semantic"],
            b["presentation"],
            b["rendering"]["rendering_subject_sha256"],
            shared["pair_subject_sha256"],
        )
        result[f"{member.lower()}-pending-receipt.json"] = receipt
        result[f"{member.lower()}-initial-publication-preparation.json"] = (
            pair.pending_preparation(
                member,
                b["semantic"],
                b["presentation"],
                receipt,
                shared["pair_subject_sha256"],
            )
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.check:
        for member in review.MEMBERS:
            review.require(
                (OUTPUT / f"{member.lower()}-rendering.json").is_file(),
                "rendered subject is missing",
            )
    for name, value in products().items():
        path = OUTPUT / name
        raw = (
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        if args.check:
            review.require(
                path.read_bytes().replace(b"\r\n", b"\n") == raw,
                "generated candidate differs: " + name,
            )
        else:
            path.write_bytes(raw)
    print(
        "bounded Health candidates: valid; owner acceptance pending; no operational authority"
    )


if __name__ == "__main__":
    main()
