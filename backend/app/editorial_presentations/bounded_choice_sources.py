"""Compare retained official captures to the distinct governed normalization.

Only whitespace, Unicode compatibility typography, quote glyphs, and spaces
before punctuation are normalized. No words, numbers or legislative meaning
are removed. This comparison never substitutes raw evidence identities.
"""

import json
import re
import unicodedata
import xml.etree.ElementTree as ET


def typography(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans("", "", "`'‘’“”\""))
    return re.sub(r"\s+([.,;:)])", r"\1", " ".join(text.split()))


def reconcile_sources(raw: dict[str, bytes], governed: dict) -> None:
    from .bounded_choice_review import require

    sources = {s["source_id"]: s for s in governed["sources"]}
    clerk = sources["clerk:119:2:180"]
    vote = ET.fromstring(raw["clerk:house:119:2:180"])
    require(vote.tag == "rollcall-vote", "Clerk source type differs")
    for key, expected in clerk["metadata"].items():
        require(
            vote.findtext(".//" + key) == expected, "Clerk metadata differs: " + key
        )
    totals = [
        {c.tag: c.text for c in row} for row in vote.findall(".//totals-by-party")
    ]
    require(totals == clerk["party_totals"], "Clerk party totals differ")
    for member, expected in clerk["member_records"].items():
        matches = [
            row
            for row in vote.findall(".//recorded-vote")
            if row.find("legislator").get("name-id") == member
        ]
        require(len(matches) == 1, "Clerk member identity differs")
        legislator = matches[0].find("legislator")
        require(
            legislator.text == expected["name"]
            and legislator.get("party") == expected["party"]
            and legislator.get("state") == expected["state"]
            and matches[0].findtext("vote") == expected["official_label"],
            "Clerk member record differs",
        )
    bill = ET.fromstring(raw["congress-text:119:s:2393:es"])
    require(
        bill.tag == "bill"
        and bill.get("bill-stage") == "Engrossed-in-Senate"
        and bill.findtext(".//legis-num") == "S. 2393",
        "exact bill version differs",
    )
    text = sources["govinfo:s2393es"]["text"]
    patterns = [
        r"SECTION 1\. SHORT TITLE\. (.*?) SEC\. 2\.",
        r"\(a\) In General\.--(.*?) \(b\)",
        r"\(b\) Authorization of Appropriations\.--(.*?) Passed the Senate",
    ]
    normalized = [re.search(p, text) for p in patterns]
    require(all(normalized), "governed bill paragraphs missing")
    paragraphs = [
        typography(" ".join(row.itertext())) for row in bill.findall(".//text")
    ]
    require(
        paragraphs == [typography(m.group(1)) for m in normalized],
        "raw and governed bill text differ",
    )
    actions = json.loads(raw["congress-actions:house:119:2:180"])
    require(
        actions["request"]["billNumber"] == "2393"
        and actions["request"]["billType"] == "s"
        and actions["request"]["congress"] == "119",
        "action source identity differs",
    )
    house = [a for a in actions["actions"] if a.get("actionCode") == "H37300"]
    require(len(house) == 1, "exact House action missing")
    action = house[0]
    require(
        action["actionDate"] == "2026-05-20"
        and action["text"]
        == "On motion to suspend the rules and pass the bill Agreed to by the Yeas and Nays: (2/3 required): 405 - 5 (Roll no. 180)."
        and action["recordedVotes"]
        == [
            {
                "chamber": "House",
                "congress": 119,
                "date": "2026-05-20T17:19:26Z",
                "rollNumber": 180,
                "sessionNumber": 2,
                "url": clerk["url"],
            }
        ],
        "exact House action differs",
    )
