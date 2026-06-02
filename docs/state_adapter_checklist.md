# State Adapter Checklist

This checklist is the gate for any state-level expansion. It prevents a state pilot from borrowing federal assumptions that do not fit state source formats, district lookup, vote subjects, or candidate data.

## 1. Scope The Pilot

- Name the state, chambers, and first ZIP or address fixture.
- State whether the pilot covers current officials, upcoming races, or both.
- Keep the first pilot to one state and one narrow user path.
- Do not merge state records into federal fingerprints, comparisons, or issue counts.

## 2. Prove District Lookup

- Identify the official district-boundary source.
- Store plan name, source URL, source date, and effective election year.
- Prefer address-level lookup for state legislative districts.
- If only ZIP-level lookup is available, label results as approximate or multi-district and do not auto-select a state legislator as the user's representative.
- Document how split ZIPs, precinct changes, and redistricting updates are handled.

## 3. Prove Current Official Identity

- Identify the official roster source for current state legislators.
- Store chamber, district, party, source URL, source date, term/session where available, and stable source identifier when available.
- Confirm whether district numbers and names match the district-boundary source.
- Define a deterministic match rule before linking a race candidate to a current official.

## 4. Prove Roll-Call Data

- Identify the official legislative vote source.
- Confirm member-level votes are available with stable roll-call identifiers.
- Store bill/session, chamber, roll-call id, vote date, vote subject, source URL, member vote, and source retrieval date.
- Exclude voice votes and committee-only actions from behavioral fingerprints unless member-level votes and scope are explicit.
- Keep procedural votes visible only when the state-specific interpretation rules support a clear evidence boundary.

## 5. Define State-Specific Vote Interpretation

- Write a state-specific interpretation note before importing interpreted vote meaning.
- Cover chamber-specific vote subjects such as second reading, third reading, concurrence, conference report, veto override, amendments, motions to table, and previous question.
- Use reviewed interpretation JSON before any public issue-read claim.
- Mark ambiguous or source-thin rows as insufficient evidence rather than converting them into support/oppose counts.

## 6. Prove Candidate And Race Context

- Identify the official state election candidate source.
- Store contest, election date, office, district, candidate name, party when available, source URL, source date, and filing/status fields when available.
- Treat candidate filing rows as election context only.
- Do not infer issue positions from candidacy or party fields.
- Link incumbents or prior officeholders only through documented deterministic match rules.

## 7. Add Separate State Storage

Use state-specific tables or clearly namespaced records before public UI:

- `state_legislators`
- `state_roll_calls`
- `state_votes_cast`
- `state_vote_interpretations`
- `state_district_maps`
- optional `state_races`
- optional `state_race_candidates`

State records must remain separate from federal `fingerprints`, `chamber_medians`, `drift_scores`, `vote_classifications`, `summaries`, and `vote_interpretations` until a deliberate cross-level methodology exists.

## 8. Product And UI Boundaries

- Label state evidence with the state and chamber, such as `NC General Assembly`.
- Keep state evidence below the federal representative accountability read until the state pilot is validated.
- Do not rank state candidates or officials.
- Do not present state stated positions as recorded governing behavior.
- Show insufficient-evidence states when source coverage is not loaded.

## 9. Go / No-Go Review

Go only when:

- district lookup is address-accurate or clearly labeled as approximate
- official roster and vote sources are stable enough to reproduce locally
- member-level roll-call votes are available
- every displayed claim has a source URL or source record
- state interpretation rules are documented before issue-read language is shown

Defer when:

- ZIP-only lookup would misidentify the user's state representative
- vote data requires fragile scraping without stable identifiers
- candidate files are incomplete or not election-ready
- interpretation would require guessing procedural effect
