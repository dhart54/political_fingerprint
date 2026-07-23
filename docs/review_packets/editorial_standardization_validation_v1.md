# Editorial standardization validation v1

This deterministic report checks contract conformance. It does not confer human approval, prove political truth, or guarantee factual perfection.

## Summary

- State: `pass`
- Fixtures: 4
- Rules: 37 (36 blocking, 1 warning)
- Findings: 0 blocking, 0 warning
- Real content remains `human_approval_pending`, `not_promoted`, and `productionEligible: false`.
- Expected production-registry entries: 0.

## Fixture results

| Fixture | Designation | State | Actions | Episodes | Featured | Not Voting | Procedural |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| foushee-economy-reference-v1 | human_reviewed_presentation_fixture | pass | 6 | 4 | 4 | 1 | 2 |
| foushee-justice-reference-v1 | human_reviewed_presentation_fixture | pass | 7 | 5 | 5 | 0 | 6 |
| massie-justice-reference-v1 | human_reviewed_presentation_fixture | pass | 7 | 5 | 5 | 0 | 6 |
| synthetic-large-record-v1 | standardization_regression_fixture | pass | 24 | 12 | 5 | 1 | 3 |

## Mutation coverage

The mutation suite contains 20 deliberate known-defect cases and requires each one to produce its expected stable rule ID. Run the suite; this generated report is not a substitute for test execution.

## Publication boundary

Reference-fixture designations are presentation and standardization contracts only. They are separate from editorial approval, benchmark promotion, production eligibility, registry inclusion, merge, and deployment.
