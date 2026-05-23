from collections import Counter, defaultdict
from typing import Any


CONTEXT_VERSION = "vote_context_v1"
VOTE_CONTEXT_POSITIONS = ("yea", "nay", "present", "not_voting")


def build_vote_contexts(
    *,
    legislators: list[dict[str, object]],
    roll_calls: list[dict[str, object]],
    votes_cast: list[dict[str, object]],
) -> list[dict[str, object]]:
    legislators_by_id = {legislator["id"]: legislator for legislator in legislators}
    roll_calls_by_id = {roll_call["id"]: roll_call for roll_call in roll_calls}
    votes_by_roll_call: dict[object, list[dict[str, object]]] = defaultdict(list)

    for vote in votes_cast:
        votes_by_roll_call[vote["roll_call_id"]].append(vote)

    contexts: list[dict[str, object]] = []
    for roll_call_id, roll_call_votes in votes_by_roll_call.items():
        roll_call = roll_calls_by_id[roll_call_id]
        total_counts = _count_positions(roll_call_votes)
        party_totals = _build_party_vote_totals(
            votes=roll_call_votes,
            legislators_by_id=legislators_by_id,
        )
        winning_position = _winning_position(total_counts)
        final_result = _final_result(winning_position)
        vote_margin = abs(total_counts["yea"] - total_counts["nay"])
        bipartisan_majority = _is_bipartisan_majority(
            party_totals=party_totals,
            winning_position=winning_position,
        )
        vote_type = infer_vote_type(
            question=str(roll_call.get("question") or ""),
            description=str(roll_call.get("description") or ""),
        )
        source_list = _build_context_source_list(roll_call)

        for vote in roll_call_votes:
            legislator = legislators_by_id[vote["legislator_id"]]
            member_party = str(legislator["party"])
            member_position = str(vote["position"])
            party_majority_position = _party_majority_position(
                party_totals=party_totals,
                party=member_party,
            )
            contexts.append(
                {
                    "roll_call_id": roll_call_id,
                    "legislator_id": vote["legislator_id"],
                    "chamber_session": roll_call.get("session"),
                    "vote_type": vote_type,
                    "member_position": member_position,
                    "final_result": final_result,
                    "vote_margin": vote_margin,
                    "winning_position": winning_position,
                    "party_vote_totals": party_totals,
                    "member_party": member_party,
                    "member_party_majority_position": party_majority_position,
                    "member_voted_with_party_majority": _matches_context_position(
                        member_position=member_position,
                        context_position=party_majority_position,
                    ),
                    "member_voted_with_winning_side": _matches_context_position(
                        member_position=member_position,
                        context_position=winning_position,
                    ),
                    "bipartisan_majority": bipartisan_majority,
                    "sponsor_party": None,
                    "context_source_list": source_list,
                    "context_version": CONTEXT_VERSION,
                }
            )

    return sorted(contexts, key=lambda row: (str(row["roll_call_id"]), str(row["legislator_id"])))


def infer_vote_type(*, question: str, description: str) -> str:
    text = f"{question} {description}".lower()

    if "nomination" in text or "confirmation" in text:
        return "nomination"
    if "amendment" in text:
        return "amendment"
    if "conference report" in text or "concur" in text:
        return "concurrence"
    if "motion" in text or "table" in text or "previous question" in text:
        return "motion"
    if "rule" in text or "providing for consideration" in text:
        return "rule"
    if "appropriation" in text or "appropriations" in text:
        return "appropriations"
    if "congressional disapproval" in text or "chapter 8 of title 5" in text:
        return "cra_disapproval"
    if "passage" in text or "on the bill" in text:
        return "final_passage"
    if "ordering" in text or "journal" in text or "quorum" in text:
        return "procedural"
    return "other"


def _count_positions(votes: list[dict[str, object]]) -> Counter:
    counts = Counter({position: 0 for position in VOTE_CONTEXT_POSITIONS})
    for vote in votes:
        counts[str(vote["position"])] += 1
    return counts


def _build_party_vote_totals(
    *,
    votes: list[dict[str, object]],
    legislators_by_id: dict[object, dict[str, object]],
) -> dict[str, dict[str, int]]:
    totals: dict[str, Counter] = defaultdict(lambda: Counter({position: 0 for position in VOTE_CONTEXT_POSITIONS}))
    for vote in votes:
        party = str(legislators_by_id[vote["legislator_id"]]["party"])
        totals[party][str(vote["position"])] += 1
    return {
        party: {position: int(counts[position]) for position in VOTE_CONTEXT_POSITIONS}
        for party, counts in sorted(totals.items())
    }


def _winning_position(counts: Counter) -> str | None:
    if counts["yea"] > counts["nay"]:
        return "yea"
    if counts["nay"] > counts["yea"]:
        return "nay"
    return None


def _final_result(winning_position: str | None) -> str:
    if winning_position == "yea":
        return "passed"
    if winning_position == "nay":
        return "failed"
    return "no_yea_nay_majority"


def _party_majority_position(*, party_totals: dict[str, dict[str, int]], party: str) -> str | None:
    totals = party_totals.get(party)
    if not totals:
        return None
    if totals["yea"] > totals["nay"]:
        return "yea"
    if totals["nay"] > totals["yea"]:
        return "nay"
    return None


def _matches_context_position(*, member_position: str, context_position: str | None) -> bool | None:
    if context_position is None or member_position not in {"yea", "nay"}:
        return None
    return member_position == context_position


def _is_bipartisan_majority(
    *,
    party_totals: dict[str, dict[str, int]],
    winning_position: str | None,
) -> bool:
    if winning_position is None:
        return False
    parties_on_winning_side = [
        party
        for party, totals in party_totals.items()
        if party in {"D", "R"} and totals.get(winning_position, 0) > 0
    ]
    return len(parties_on_winning_side) >= 2


def _build_context_source_list(roll_call: dict[str, object]) -> list[dict[str, str]]:
    source_url = roll_call.get("source_url")
    if not source_url:
        return []
    return [
        {
            "source_type": "official_roll_call",
            "url": str(source_url),
        }
    ]
