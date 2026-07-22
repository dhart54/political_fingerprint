# Justice Cross-Member Cohort Selection V1

## Method

The selection used only official recorded actions on substantive rolls 32, 33, 130, 131, 166, 275, and 299. Inputs were Yes/No completeness, episode-level differences, within-fentanyl trajectory differences, vote-vector diversity, and edge-case usefulness. Party was retained only as descriptive metadata; ideology scores, public reputation, fame, caucus labels, campaign statements, and external ratings were excluded.

The official union contains 437 House members who appeared on at least one reviewed roll. Of those, 370 have seven Yes/No actions and 31 have six. `docs/editorial/justice_cross_member_validation_v1/cohort_selection.json` documents every considered member, vote vector, coverage, selection flag, and exclusion reason. After a vector was chosen for validation value, the smallest Bioguide ID broke ties unless the Foushee reference was required.

## Selected cohort

Roll order is `32 / 33 / 130 / 131 / 166 / 275 / 299`.

| Member | Party metadata | Vote vector | Validation contribution |
| --- | --- | --- | --- |
| Valerie P. Foushee (`F000477`) | D | Y/N/N/Y/Y/N/N | Reference record from PR #95. |
| Alma S. Adams (`A000370`) | D | Y/N/N/Y/Y/N/N | Exact-vector equivalence and identity-preservation case. |
| Robert B. Aderholt (`A000055`) | R | N/Y/Y/Y/Y/Y/Y | Dominant complete vector; contrasts with the reference on six rolls. |
| Thomas Massie (`M001184`) | R | N/N/Y/Y/N/Y/Y | Unique complete Republican vector; separates the fentanyl episode from police tools and authority. |
| Sanford D. Bishop, Jr. (`B000490`) | D | N/Y/Y/Y/Y/N/N | Different fentanyl trajectory with a repeated boundary at the two D.C. episodes. |
| Jesús G. “Chuy” García (`G000586`) | D | N/N/N/N/N/N/N | Unique complete all-Nay vector across distinct mechanisms. |
| Jared Moskowitz (`M001217`) | D | Y/Y/Y/Y/Y/Y/N | Unique mostly-Yea vector with a material safeguard-repeal exception. |

All seven selected members have 7/7 substantive Yes/No actions and 5/5 complete independent episodes. No selected member has a missing, Present, or Not Voting action in the substantive set. Synthetic tests cover those absence states without weakening the real-cohort completeness standard.

Members not selected were not needed after these seven records covered exact equivalence, dominant contrast, distinct fentanyl sequences, split police mechanisms, one-directional opposition, broad support with contrary evidence, and a Republican outlier. Exclusion does not imply similarity, quality, or rank.
