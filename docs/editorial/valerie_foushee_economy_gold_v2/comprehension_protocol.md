# Reader comprehension protocol

This protocol has not been run. It defines the pending human research needed before any candidate can be approved.

## Participants and setup

- Recruit nonexpert U.S. adults who do not work in Congress or legislative advocacy.
- Test one roll at a time; randomize roll order across participants.
- Show only the proposed public layer being evaluated. Do not explain procedural terms before the retell.
- Ask for an unaided retell after one reading, then probe with the five standard questions.
- Record answers verbatim, misconceptions, hesitation, and which layer was visible.

## Five standard questions

1. What was Congress deciding?
2. What would have changed?
3. Who or what was affected?
4. What did Foushee do?
5. Did the measure become law, remain intermediate, or fail?

Expected answers, acceptable equivalents, likely misconceptions, and supplying fields are specified for every candidate in `review_packet.json`.

## Field-level scoring

For each question, record:

- `correct_without_prompt`
- `correct_after_neutral_probe`
- `partly_correct`
- `incorrect`
- `not_answered`

Also record whether the reader:

- confused Not Voting with No;
- confused House passage with enactment;
- merged two stages of the same measure;
- treated a budget framework as the later law;
- inferred motive or a broad ideology;
- could name the affected group; and
- could state the real-world mechanism rather than repeat the title.

## Revision gate

Request changes when a repeatable misconception appears, when the affected group or lifecycle status cannot be recalled, or when the reader can repeat the title but cannot explain the choice. Additional length alone is not an acceptable fix. Re-test any changed top-layer field.

## Completion boundary

The packet remains `human_approval_pending` until sessions are conducted and reviewed. A readability score or automated diagnostic cannot substitute for this protocol.
