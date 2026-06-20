# 118th House Amendment Evidence Public Validation

Validation date: 2026-06-20

## Backend Public API

- Backend: `https://political-fingerprint.onrender.com`
- Health: `ok`
- Metadata: `data_source=database`, `window_end=2026-06-19`, `eligible_roll_call_count=627`, `classification_version=v1`

Representative checks:

| Official | Legislator ID | Expected scope behavior | Observed |
| --- | --- | --- | --- |
| Valerie P. Foushee | `leg_valerie_p_foushee` | Current House member with 118th and 119th records | `scope=118` interpreted sum 305; `scope=119` interpreted sum 70; `scope=all` interpreted sum 375; 118th evidence rows 170 |
| Aaron Bean | `leg_aaron_bean` | Current House member with 118th and 119th records | `scope=118` interpreted sum 305; `scope=119` interpreted sum 70; `scope=all` interpreted sum 375; 118th evidence rows 170 |
| Colin Allred | `leg_allred` | Former 118th House member without 119th House record | `scope=118` interpreted sum 305; `scope=119` interpreted sum 0; `scope=all` interpreted sum 305; 118th evidence rows 170 |
| Abraham J. Hamadeh | `leg_abraham_j_hamadeh` | 119th-only current House member | `scope=118` interpreted sum 0; `scope=119` interpreted sum 70; `scope=all` interpreted sum 70; 118th evidence rows 0 |
| Earl Blumenauer | `leg_blumenauer` | Former 118th House member | `scope=118` interpreted sum 305; `scope=119` interpreted sum 0; `scope=all` interpreted sum 305; 118th evidence rows 170 |

For checked 118th evidence responses, returned congresses were `["118"]` with status distribution `interpreted=124` and `insufficient_evidence=46`.

## Rendered Frontend

- Frontend: `https://political-fingerprint.vercel.app/`
- Browser title: `Political Fingerprint`
- Loaded hero: `Voting record, explained.`
- Rendered public totals included `560 LEGISLATORS`, `627 ROLL CALLS`, and `100% SOURCE LINKS`.
- ZIP `27701` rendered as mapping to `NC-04` with Valerie P. Foushee, Ted Budd, and Thom Tillis loaded for inspection.

Scope controls:

| Control | Observed active state | Observed helper text |
| --- | --- | --- |
| Full Record | `FULL RECORD 118th + 119th` active | Full record view rendered without a scope-only helper line |
| Recent Congress | `RECENT CONGRESS 119th` active | `Showing the recent Congress view only.` |
| Prior Congress | `PRIOR CONGRESS 118th` active | `Showing the prior Congress view only.` |

Rendered validation confirms the deployed frontend reads the post-write public API totals and that `scope=118`, `scope=119`, and full-record controls remain interactive. No runtime code changed in this milestone.
