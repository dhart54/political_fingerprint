# Full-Record Action Interpretation Decision Authority V1

## Purpose

This contract generalizes the accepted Justice action-interpretation
authority-to-implementation pattern for a complete full-record candidate batch.
It records an immutable human decision, binds every accepted candidate by
content digest, and deterministically implements only the accepted exact-action
meaning, exact-choice position effect, confidence, limitations, coverage, and
source mappings.

The governing schemas are:

- `full_record_action_interpretation_authority_v1.schema.json`
- `full_record_action_interpretation_decision_implementation_v1.schema.json`
- `full_record_action_interpretation_implementation_parity_v1.schema.json`

The reusable implementation is
`backend/app/etl/full_record_action_interpretation_decisions.py`.

## Authority requirements

The authority record must bind the reviewer and reviewer authority, UTC decision
timestamp, accepted PR and head, exact post-merge main, candidate artifact ID,
candidate file and subject digests, decision-template identity, upstream
universe and readiness bindings, all accepted candidate and evidence-map
digests, and every preserved limitation.

Each accepted decision must equal its candidate as written. A source-blocked
action cannot receive an authority decision or implementation record.

## Internal canonical boundary

Human acceptance makes the implemented action meanings canonical internal
action-interpretation inputs. This is the same bounded distinction used by the
accepted Justice decision-authority architecture:

- internal action interpretation may be human accepted and canonical;
- canonical Semantic IR acceptance remains false;
- policy-episode construction and acceptance remain separately authorized;
- public wording, publication, persistence, production, and deployment remain
  false.

Detailed accepted meanings are internal evidence-backed semantic inputs. Later
public wording must be separately reviewed, concise by default, and use
progressive disclosure for detailed meaning and sources.

## Deterministic implementation

Every implementation record must reproduce its authority decision exactly and
bind the authority artifact, authority decision, candidate, evidence map, and
source references. The implementation may not revise wording, confidence,
limitations, coverage, or position effect.

Independent validation must recompute all decision and record digests, prove
exact action-set equality, preserve blocked actions, validate schemas and final
file parity, and fail closed if any downstream authorization becomes true.
