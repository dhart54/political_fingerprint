# M12J/K Environment & Energy Synthesis Acceptance and Public Wording V1

## Intent

Mechanically implement the independently accepted M12I synthesis candidate
without changing it, validate M12J completely, and only then compile five
detached public-wording candidates under Selected Issue Experience V1.1.

## Exact boundary

- Accepted PR #154 head: `95a7c59cd1876c7934fea9547008e2b8e86e8be0`.
- Reviewed base: `d3bc0fddad701e0621c87857ed80288c23a867aa`.
- Exact post-M12I merge main:
  `ea6b93cd51110dd2e8da71448ce2a5b14f864ba3`.
- In scope: generic synthesis-decision and public-wording contract corrections,
  exact M12J acceptance, independent validation, detached M12K candidates,
  complete limitation accounting, regressions, one branch, and one draft PR.
- Out of scope: M12L acceptance, M12M site integration, M12N publication,
  persistence, database or production writes, deployment, and the two protected
  user-owned ZIPs.

## Internal gates

1. Guarded-merge exact PR #154 and branch from exact resulting main.
2. Generalize synthesis authority/implementation bindings while preserving the
   byte-identical M11J package and complete 63-episode disposition ledger.
3. Accept the sole M12I synthesis candidate as written and independently
   validate M12J before generating wording.
4. Generalize public-wording semantic bindings and zero-or-more blocked-action
   boundaries while preserving byte-identical M11K output.
5. Compile exactly five detached wording candidates, validate their semantic
   ownership and complete limitation treatment, then stop for substantive review.

## Completed M12J gate

- [x] One exact `accept_candidate_as_written` decision; no bounded revision.
- [x] The complete reviewed synthesis candidate remains structurally and
  semantically unchanged, including candidate-era unresolved ambiguity.
- [x] Three Behavioral Semantic IR inputs and 13 deduplicated episode/action
  lineage records remain exact.
- [x] The complete 63-episode ledger includes the separate one-episode unused
  non-directional category.
- [x] Historical M11J artifacts remain byte-identical and valid.
- [x] M12J was independently validated before M12K generation.

## M12K review frontier

- [x] Exactly one issue overview, one synthesis item, and three repeated-pattern
  items; zero trajectory and notable-choice items.
- [x] Every accepted M12H proposition and the accepted M12J synthesis has
  exactly one primary wording owner.
- [x] All five sentences state opposition to congressional efforts to overturn
  the underlying decisions; none converts that relationship into affirmative
  unrestricted support.
- [x] Standalone direction display is omitted from every item so the object of
  opposition remains explicit in the sentence.
- [x] Every source limitation has an explicit retained or compressed treatment.
- [x] Environment has zero blocked actions and no fake boundary is introduced.
- [x] The human decision template is entirely empty and all downstream authority
  remains false.
- [ ] Draft PR hosted checks pass on the exact final head.

## Validation approach

Run M12A-K validators, historical M11A-N and Justice regressions, Behavioral
Semantic IR, synthesis, public-wording and presentation suites, Selected Issue
Experience and publication/API regressions, schema/JSON/docs/terminology, Ruff,
formatting, compilation, ancestry/scoped-diff checks, and `git diff --check`.
Unchanged Windows checkout byte/line-ending failures remain baseline-only;
hosted Linux CI is the broad authoritative gate.

## Stop condition

Stop at the combined draft PR for independent substantive review of M12K. Do
not begin M12L, site integration, publication, persistence, production, or
deployment.
