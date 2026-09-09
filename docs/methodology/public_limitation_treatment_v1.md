# Governed public receipt limitations V1

Future reviewed receipt projections supply `limitation_treatments`, covering every
exact source caveat in order. Each entry has exactly `source_text`, `treatment`
(`public` or `internal`) and `public_copy`. Public entries require authored copy;
internal entries require empty copy. Process and provenance share one internal
state because rendering does not need to distinguish them.

The backend validates complete coverage and projects `public_caveats`. If both
forms are supplied they must agree. An explicit `public_caveats` list is
authoritative, including an empty list; the frontend must not substitute a legacy
fallback or reclassify it using process vocabulary. The frontend may consume
structured treatments directly at detached review boundaries.

Public copy is an editorial input. A mixed sentence such as “The reviewed
interpretation remains a candidate because implementation depends on incomplete
official amendment text” may use explicitly authored “Official amendment text is
incomplete” after appropriate semantic review. JavaScript never extracts that
clause, invents copy, or confers approval. Synthetic tests demonstrate this shape;
they do not assert an incomplete-text finding about a real member.

Legacy untyped caveats remain conservative. Keep potentially substantive text,
including `reviewed`, `candidate`, `implementation`, `accepted` and `milestone`.
Suppress only complete known process boilerplate (such as a standalone dated
human-review statement) and unmistakable structural internals: repository paths,
hashes, raw artifact references and internal IDs. Never extend a vocabulary
blocklist to hide new governance phrases; give actual affected text an explicit
upstream treatment instead. Structural defense remains for explicit public copy.

The bounded live inventory found 35 occurrences of one Justice limitation, hidden
by the old generic-candidate prefix. It limits motive, ideology, broad issue
positions and synthesis inference. The noun “candidate” does not report process
state. All 35 proposed treatments are PUBLIC with exact unchanged source copy.
No active mixed-copy rewrite or internal-only treatment was needed. The complete
affected set and old/new render output are in the M15B review directory. This is
pending independent review; no historical artifact or publication is rewritten.
