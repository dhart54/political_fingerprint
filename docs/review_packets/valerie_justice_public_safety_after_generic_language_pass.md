# Valerie Foushee Justice/Public Safety After Generic Language Pass

Generated: 2026-06-02

Scope: narrow implementation pass on Valerie P. Foushee / `JUSTICE_PUBLIC_SAFETY`. This pass fixes reusable generic overview and fallback card-summary language. It does not add new interpretation coverage, does not add curated roll-number summaries for Justice/Public Safety, and does not broad-rollout to other domains.

API source checked locally: `http://127.0.0.1:8000/legislators/leg_valerie_p_foushee/positions/JUSTICE_PUBLIC_SAFETY/evidence`

## 1. Final Rendered Issue Overview

```text
What these votes were about
In this Justice & Public Safety sample, the reviewed votes where Foushee cast a Yes or No covered several public-safety and legal-policy questions: whether to permanently schedule fentanyl-related substances and apply related penalty-threshold and research-registration changes; whether to create a program for federal law-enforcement officers to buy retired agency-issued firearms; whether to require DOJ reporting on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources; whether to change D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with exceptions; and whether to repeal D.C.'s 2022 policing and justice reform act and restore provisions changed by that act. Seven additional rows remain visible below but are not counted because the available source text does not clearly explain the practical policy effect.

What Foushee did
Of the 6 reviewed Yes/No votes that could be interpreted, 2 supported the measures shown and 4 opposed them. All of those votes matched most Democrats. Most opposed measures that passed the House.

What pattern that creates
Foushee's reviewed votes where she cast a Yes or No in this sample were mixed. Her record here is best read as a mixed record on this specific set of Republican-led House measures, not as a simple statement that she is broadly for or against this issue area.

How a voter might read that
If you generally favored these House Republican measures, this section may look misaligned with your views. If you generally wanted Democrats to oppose those measures or objected to their terms, this section may look aligned. The vote record alone does not show her motive.

What not to infer
Do not infer motive, ideology, character, corruption, or a voting recommendation from this section. The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area. Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.
```

## 2. Derived Issue-Overview Object Excerpt

```json
{
  "issueLabel": "Justice & Public Safety",
  "representativeLabel": "Foushee",
  "measureGroups": [
    {
      "id": "fentanyl_scheduling_and_penalties",
      "label": "fentanyl scheduling and penalty thresholds",
      "rowCount": 2,
      "positions": { "nay": 1, "yea": 1 }
    },
    {
      "id": "federal_law_enforcement_equipment",
      "label": "federal law-enforcement retired weapon purchases",
      "rowCount": 1,
      "positions": { "nay": 1 }
    },
    {
      "id": "law_enforcement_safety_reporting",
      "label": "law-enforcement safety reporting",
      "rowCount": 1,
      "positions": { "yea": 1 }
    },
    {
      "id": "dc_police_pursuit_policy",
      "label": "D.C. police pursuit policy",
      "rowCount": 1,
      "positions": { "nay": 1 }
    },
    {
      "id": "dc_policing_reform_repeal",
      "label": "D.C. policing reform repeal",
      "rowCount": 1,
      "positions": { "nay": 1 }
    }
  ],
  "votePattern": {
    "interpretedYesNoCount": 6,
    "supportCount": 2,
    "opposeCount": 4,
    "notVotingCount": 0,
    "ambiguousCount": 7,
    "partyComparedCount": 6,
    "partyMatchCount": 6,
    "finalOutcomeComparedCount": 6,
    "finalOutcomeMatchCount": 2,
    "finalOutcomeAgainstCount": 4,
    "predominantPosition": "mixed interpreted vote pattern"
  }
}
```

## 3. First Three Default-Visible Card Summaries

### Roll 32

```text
Yea. The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
```

### Roll 33

```text
Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.
```

### Roll 130

```text
Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.
```

## 4. Limited/Insufficient Row Treatment

Roll 32 is ambiguous and remains visible by default with this caveat:

```text
Yea. The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
```

The overview counts seven ambiguous or limited-context rows and excludes them from support/opposition counts.

## 5. API/Evidence Row Excerpt

```json
[
  {
    "rollcall_number": 32,
    "position": "yea",
    "interpretation_status": "ambiguous",
    "issue_facet": "administrative_law_and_regulatory_procedures"
  },
  {
    "rollcall_number": 33,
    "position": "nay",
    "interpretation_status": "interpreted",
    "issue_facet": "fentanyl_scheduling_and_penalties"
  },
  {
    "rollcall_number": 130,
    "position": "nay",
    "interpretation_status": "interpreted",
    "issue_facet": "federal_law_enforcement_equipment"
  }
]
```

## 6. Tests Run

```text
node --test frontend/lib/issueOverview.test.mjs
Result: pass, 6 tests passing.

npm run build
Result: pass. Next.js compiled successfully and generated 4 static pages.
```

No backend tests were run because this pass did not change the backend API or object shape.

## 7. Files Changed

- `docs/methodology.md`
- `docs/review_packets/valerie_justice_public_safety_current_state.md`
- `docs/review_packets/valerie_justice_public_safety_after_generic_language_pass.md`
- `frontend/components/PositionByIssue.js`
- `frontend/lib/issueOverview.mjs`
- `frontend/lib/issueOverview.test.mjs`
- `frontend/lib/voteCardSummary.mjs`

## 8. Known Limitations

- Justice/Public Safety still uses generic card summaries, not curated roll-number summaries.
- Ambiguous groups still display fallback facet labels such as `house of representatives`; that is visible as an evidence limit, not as a interpreted measure group.
- The reusable overview foundation now handles domain-aware language and known Justice measure-group labels, but this is not a broad rollout across all domains.
