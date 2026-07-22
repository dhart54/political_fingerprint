# Justice Cross-Member Cohort Selection V1

Selection used official recorded actions on rolls 32, 33, 130, 131, 166, 275, and 299. Inputs were Yes/No completeness, episode-level differences, fentanyl trajectory differences, diversity of action structures, and validation usefulness. Party is retained only as descriptive metadata; ideology, reputation, fame, caucus, campaign statements, and external ratings were excluded.

The official union contains 437 House members; 370 have seven Yes/No actions. `cohort_selection.json` documents every considered member. After an action structure was selected for validation value, the smallest Bioguide ID broke ties unless the Foushee reference was required.

| Member | Party metadata | Actions (32/33/130/131/166/275/299) | Validation contribution |
| --- | --- | --- | --- |
| Valerie P. Foushee (`F000477`) | D | Y/N/N/Y/Y/N/N | Reference action structure from PR #95. |
| Alma S. Adams (`A000370`) | D | Y/N/N/Y/Y/N/N | Equivalent-action and identity-preservation case. |
| Robert B. Aderholt (`A000055`) | R | N/Y/Y/Y/Y/Y/Y | Dominant action contrast; differs from the reference on six rolls. |
| Thomas Massie (`M001184`) | R | N/N/Y/Y/N/Y/Y | Fentanyl-versus-police-action split. |
| Sanford D. Bishop, Jr. (`B000490`) | D | N/Y/Y/Y/Y/N/N | National-versus-D.C. action boundary. |
| Jesús G. “Chuy” García (`G000586`) | D | N/N/N/N/N/N/N | Cross-mechanism opposition structure. |
| Jared Moskowitz (`M001217`) | D | Y/Y/Y/Y/Y/Y/N | Broad support with a safeguard-repeal exception. |

All selected members have 7/7 Yes/No actions and 5/5 complete independent episodes. Synthetic tests cover missing, Present, and Not Voting without shrinking expected coverage. Exclusion implies neither similarity nor rank.
