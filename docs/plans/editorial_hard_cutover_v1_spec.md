# Milestone: Political Fingerprint Repository Editorial Hard Cutover V1

Repository:

`dhart54/political_fingerprint`

Exact base commit:

`bc7617b05f33d56cf83c4bb7e4b8113b945a3998`

Create and work on a dedicated branch such as:

`codex/editorial-hard-cutover-v1`

## Required preread

Before modifying files, read:

* `AGENTS.md`
* `docs/interpretation_principles.md`
* `docs/architecture/editorial_pipeline_v1_handoff.md`
* `docs/architecture/editorial_pipeline_inventory_v1.json`
* `docs/editorial/current_state_index.json`
* `docs/semantic_ir/editorial_semantic_ir_v1.md`
* `docs/workflows/editorial-standardization-pipeline.md`
* `docs/public_editorial_frontend_contract.md`
* `docs/design/editorial_artifact_persistence_contract_v1.md`
* `docs/workflows/codex-operating-model.md`

The user’s current milestone instructions supersede PR #111’s earlier decision to retain obsolete executable paths for replay compatibility and retain the old public editorial architecture as a fallback.

## Intent

Perform a deliberate repository hard cutover from the obsolete pre-Semantic-IR editorial architecture.

Backward compatibility with the old editorial format is not required.

It is acceptable and intended for the old rich editorial website enhancements to be temporarily removed. Do not replace them with a new IR-native public editorial experience in this milestone.

The application must remain intentionally functional in its reduced state:

* basic vote evidence still renders;
* vote receipts remain available;
* old editorial enhancements are absent;
* removed editorial routes are either deleted or return a deliberate unavailable or unsupported result;
* the frontend builds and starts successfully;
* no dangling imports, runtime 500 errors, or accidental broken states remain;
* unrelated product areas remain functional.

## Required outcome

At milestone completion:

1. Editorial Semantic IR V1 remains the only executable editorial semantic architecture.
2. Obsolete pre-IR semantic transformation, inference, conclusion, ownership, and routing code is deleted.
3. Milestone-specific executable editorial builders are deleted when they are no longer required by canonical validation or protected acquisition capability.
4. The old-format frontend editorial runtime, components, selectors, registries, fixtures, and review harnesses are removed.
5. The application deliberately falls back to the basic vote-evidence experience rather than failing accidentally.
6. Historical evidence and provenance remain preserved without requiring executable legacy replay.
7. Useful semantic, acquisition, provenance, and artifact-integrity test coverage is transferred before obsolete tests and implementations are deleted.
8. Source-acquisition capabilities remain intact, including currently unused capabilities.
9. Production persistence, publication, migrations, deployment, and database state remain unchanged.
10. Canonical semantic validation and the surviving non-editorial product surface remain healthy.

## Authority and preservation model

Preserve the authority and evidentiary role of the durable architectural documents, not necessarily their exact bytes.

The following documents must be updated where necessary to describe the post-cutover repository accurately:

* `docs/architecture/editorial_pipeline_v1_handoff.md`
* `docs/architecture/editorial_pipeline_inventory_v1.json`
* `docs/editorial/current_state_index.json`
* workflow documentation that still identifies deleted paths as historical replay implementations or retained public fallbacks;
* corresponding human-readable mirrors, when they remain part of repository governance.

Statements from PR #111 that legacy builders remain executable for replay or that old public adapters remain retained fallbacks must not survive after those paths are deleted.

Do not preserve obsolete descriptions merely to minimize documentation diffs.

## Hard evidence-preservation boundary

The following should generally remain byte-stable unless a concrete integrity repair is required and separately justified:

* accepted development semantic references;
* accepted held-out semantic references;
* acceptance receipts;
* answer-free held-out inputs;
* held-out first-pass proof artifacts;
* correction-cycle proof artifacts;
* dossiers;
* measure and action source manifests;
* proof packets;
* provenance records;
* preservation receipts;
* raw downloaded source data;
* raw archives;
* source locators;
* stable source, claim, action, episode, family, and member identifiers.

Do not rewrite historical evidence into the new format.

Do not regenerate historical outputs using the canonical pipeline.

Do not remove frozen historical artifacts merely because the executable builder that created them is removed.

## Canonical architecture to preserve

Do not delete or weaken:

* `backend/app/semantic_ir/compiler.py`;
* `backend/app/semantic_ir/pipeline.py`;
* `backend/app/semantic_ir/validation.py`;
* meaning-preserving canonical adapters;
* the Semantic IR schema;
* accepted-reference comparison tooling;
* canonical semantic, domain, and release validation commands;
* tests protecting the canonical compiler, input-only boundary, accepted references, invariance, action accounting, coverage, review routing, and adapter isolation.

Do not change accepted semantic outcomes, compiler methodology, proposition rules, synthesis rules, coverage semantics, action accounting, review routing semantics, or civic-integrity rules in this milestone.

## Source-acquisition preservation boundary

Preserve all source-acquisition capability, including capability that is currently unused by the canonical pipeline.

This includes:

* source clients;
* scrapers;
* downloaders;
* parsers;
* pagination;
* retries and backoff;
* caching;
* raw response handling;
* canonicalization;
* normalization;
* stable identifier creation;
* source and claim mapping;
* raw storage;
* archive handling;
* acquisition fixtures;
* acquisition tests;
* source-integrity tests.

Do not classify an acquisition path as obsolete merely because no currently commissioned Semantic IR workflow calls it.

Before deleting any ambiguous module, determine whether it acquires, downloads, parses, normalizes, caches, identifies, maps, archives, or stores source evidence. If it does, preserve it or safely separate the acquisition responsibility from the obsolete editorial responsibility.

## Production persistence and recovery boundary

Do not delete or substantially alter:

* production migrations;
* migration `0016` or later editorial persistence migrations;
* `backend/app/editorial_artifacts/`;
* `backend/scripts/editorial_artifact_store.py`;
* persistence import tooling;
* deterministic export tooling;
* backup preparation;
* rollback tooling;
* manifest hashing;
* reconciliation;
* post-write validation;
* production dependency-discovery capability;
* the historical persistence seed manifest;
* the persistence review packet;
* immutable production audit history.

This milestone must not connect to or query production.

Production database table removal is a later milestone requiring:

1. read-only live dependency discovery;
2. exact table and consumer inventory;
3. validated backups;
4. export and rollback preparation;
5. expected-impact analysis;
6. explicit user review;
7. separate destructive authorization.

Do not remove operational recovery or inspection tooling merely because it consumes the historical persistence representation.

## Authorized deletion classes

Delete obsolete executable code in these classes after tracing its direct and transitive dependents:

* pre-IR exact-action editorial eligibility builders;
* pre-IR member overlay and coverage builders;
* legacy editorial inference and proposition builders;
* legacy conclusion synthesis;
* legacy section ownership and rendered-text deduplication;
* legacy review-routing builders;
* milestone-specific Economy, Justice, and Environment editorial generators;
* old-format persistence-proposal construction owned by those generators;
* old editorial frontend selectors and experience adapters;
* old public and review presentation adapters;
* old editorial React components;
* old review, production, commissioning, and test registries;
* old editorial golden-render fixtures and harness-only code;
* old-format editorial API routes or serializers that are not shared evidence APIs;
* compatibility shims whose only purpose is supporting the deleted editorial format;
* tests that exist solely to assert obsolete implementation behavior after useful protection has been transferred.

The existing inventory is a discovery starting point, not an exhaustive deletion allowlist.

Do not leave dead compatibility modules, empty registries, placeholder legacy adapters, or unreachable old-format code solely for backward compatibility.

## Legacy test classification and coverage transfer

Do not delete a legacy test merely because it executes obsolete code.

Before deleting or rewriting each affected test, classify it as exactly one of:

1. `obsolete_implementation_test`

   * Protects only the behavior or internal structure of an implementation being deleted.
   * May be removed with the implementation after confirming it contains no independent invariant.

2. `semantic_invariant_already_covered`

   * Protects a useful semantic or civic-integrity rule already covered by the 16 accepted references, canonical compiler tests, property tests, or boundary tests.
   * Record the replacement coverage location before deleting the legacy test.

3. `acquisition_or_provenance_protection`

   * Protects source retrieval, parsing, stable identifiers, mappings, manifests, provenance, dossier integrity, or evidence preservation.
   * Must remain, or must be transferred to a test that does not require obsolete editorial execution.

4. `historical_artifact_integrity`

   * Protects frozen historical artifacts, proof packets, receipts, or expected archived relationships.
   * Rewrite it to validate frozen files directly rather than invoking the deleted generator.

For each deleted legacy test, record:

* its classification;
* the useful invariant, if any;
* the replacement test or canonical coverage location;
* whether the replacement validates code behavior, acquisition capability, or frozen historical evidence.

The goal is not to preserve obsolete code for the sake of tests. The goal is to preserve all useful protection before removing obsolete code and tests.

## Historical artifact-integrity strategy

Where useful historical protection currently depends on executing a deleted builder, replace it with direct validation of frozen evidence.

Appropriate static checks include:

* required-file existence;
* JSON parsing;
* schema validation;
* manifest-to-file reference integrity;
* manifest path resolution;
* recorded hash or checksum verification;
* source and claim locator preservation;
* stable identifier preservation;
* expected artifact counts;
* expected relationship counts;
* receipt-to-manifest consistency;
* accepted-reference source-reference resolution;
* proof-packet completeness;
* preservation-receipt integrity.

Static historical validation must not:

* recompute obsolete editorial conclusions;
* imply current semantic authority;
* promote historical outputs to canonical inputs;
* rewrite frozen files;
* require deleted generators.

## Frontend cutover behavior

Removing the rich editorial surface is authorized. Breaking the application accidentally is not.

The desired interim behavior is:

* representative and issue pages still load;
* basic vote evidence still renders;
* existing vote receipts still render;
* procedural, limited-context, Present, Not Voting, and missing-evidence distinctions remain intact;
* no broad editorial conclusion is reconstructed from raw vote counts in React;
* no old editorial selector, registry, inference object, or presentation adapter is used;
* old rich-editorial-only routes are removed or return an intentional unavailable/not-supported response;
* old review routes and fixture pages do not silently expose stale content;
* the application builds successfully;
* the application starts successfully;
* no dangling imports remain;
* no known user path returns an accidental 500 due to the cutover;
* unrelated pages and product capabilities remain functional.

Prefer deleting old routes when no compatibility value remains.

Where a route must remain for structural reasons, return a deliberate and testable result such as:

* HTTP 404 when the route no longer exists;
* HTTP 410 when explicitly representing a removed resource;
* a bounded “editorial experience not currently available” state;
* the standard basic-evidence fallback.

Do not introduce a new editorial design or new public analytical copy in this milestone.

## Discovery requirements

Before modifying files:

1. Confirm the exact base commit.
2. Confirm branch and worktree state.
3. Read all applicable scoped `AGENTS.md` files.
4. Build a direct and transitive dependency map for:

   * the six legacy summary modules in the current inventory;
   * all milestone-specific editorial builders;
   * all frontend editorial components;
   * all frontend editorial libraries;
   * all production, review, commissioning, and test registries;
   * all editorial routes and fixture routes;
   * all old-format API and serialization paths;
   * all old-format persistence-proposal builders;
   * all tests that import or execute these paths.
5. Separately inventory all source-acquisition files and tests that must be protected.
6. Separately inventory all production recovery, export, rollback, and dependency-discovery tooling that must be protected.
7. Classify each relevant path as:

   * `canonical_semantic`;
   * `retained_acquisition`;
   * `retained_historical_evidence`;
   * `retained_live_persistence_safety`;
   * `remove_legacy_execution`;
   * `unrelated`;
   * `blocking_requires_review`.
8. Classify every affected legacy test using the required four-part test classification.
9. Produce a proposed deletion set and coverage-transfer map before applying deletions.
10. Identify the exact intended frontend fallback behavior and route behavior before implementation.

Do not expand into general repository cleanup.

## Implementation requirements

* Remove obsolete imports and call sites rather than leaving dead compatibility shims.
* Do not add adapters from Semantic IR back into the old editorial format.
* Do not retain empty legacy registries solely for backward compatibility.
* Remove the old rich editorial branch from the representative-page runtime.
* Preserve the basic issue evidence, position evidence, and vote receipt paths.
* Deliberately remove or fail closed any old rich-editorial-only route.
* Replace useful legacy test protection before deleting the corresponding test.
* Replace generator-dependent historical tests with frozen-file integrity validation.
* Add focused negative dependency tests proving surviving executable code cannot import deleted legacy paths.
* Add tests proving canonical commands do not import deleted legacy modules.
* Add tests proving the frontend fallback does not reconstruct analytical meaning from raw evidence.
* Add tests proving old routes are absent or deliberately unavailable.
* Add tests proving the application builds without old registries, selectors, or components.
* Keep canonical adapters meaning-preserving and non-authoritative.
* Do not introduce new editorial prose, conclusions, findings, or publication state.
* Do not modify accepted references to make validation pass.
* Do not weaken a civic-integrity invariant to preserve old behavior.

## Documentation updates

Update the durable architectural documents to describe the completed cutover accurately.

At minimum, update:

* `docs/architecture/editorial_pipeline_v1_handoff.md`;
* `docs/architecture/editorial_pipeline_inventory_v1.json`;
* the corresponding human-readable architecture inventory, if retained;
* `docs/editorial/current_state_index.json`;
* the corresponding human-readable state index, if retained;
* `docs/semantic_ir/editorial_semantic_ir_v1.md`, where legacy-runtime or fallback statements become inaccurate;
* `docs/workflows/editorial-standardization-pipeline.md`;
* frontend workflow documentation that still describes the deleted rich editorial runtime;
* `AGENTS.md`, only where durable hard-cutover, acquisition-preservation, test-transfer, or frontend-fallback rules belong.

The updated documents must distinguish:

* canonical executable architecture;
* preserved acquisition capability;
* preserved historical evidence;
* preserved live persistence and recovery capability;
* deleted legacy execution;
* temporary basic-evidence frontend behavior;
* deferred IR-native presentation work;
* deferred database cleanup.

Do not state that legacy builders remain available for replay if they are deleted.

Do not state that old public adapters remain retained fallbacks if they are deleted.

Do not imply that preserved historical artifacts are canonical semantic inputs.

## Cutover receipt

Add a machine-readable cutover receipt containing:

* schema version;
* base commit;
* branch or milestone identifier;
* deleted executable paths;
* deleted test paths;
* test classification for every deleted or rewritten legacy test;
* replacement coverage location for every transferred useful invariant;
* preserved accepted corpora and receipts;
* preserved historical-evidence roots;
* preserved acquisition roots and capabilities;
* preserved persistence and recovery paths;
* removed frontend routes;
* deliberately retained frontend fallback routes;
* validation commands;
* validation outcomes;
* confirmation that the frontend builds and starts;
* confirmation that no dangling imports remain;
* confirmation that accepted semantic references were unchanged;
* confirmation that production was not queried;
* confirmation that persistence, publication, deployment, and database state were untouched.

## Validation

Use the narrowest sufficient checks during implementation.

Final validation must include:

```powershell
python scripts/run_editorial_pipeline.py validate --tier semantic
```

Run representative canonical domain and case validation through the same public pipeline.

Because frontend runtime changes, run the applicable frontend unit tests and production build.

Frontend validation must cover:

* basic evidence rendering;
* vote receipt rendering;
* representative selection;
* issue selection;
* procedural and limited-context handling;
* Present and Not Voting handling;
* missing-evidence behavior;
* removal of old editorial selectors and registries;
* removal or deliberate unavailability of old editorial routes;
* no broad conclusion inferred in React;
* no dangling imports;
* successful application build;
* successful application startup or bounded smoke test;
* no accidental 500 on tested surviving routes;
* unrelated critical product routes still functioning.

Run the release tier with frontend validation when supported:

```powershell
python scripts/run_editorial_pipeline.py validate --tier release --include-frontend
```

Do not use `--include-persistence` unless a purely local, read-only persistence validation is required by an unchanged protected path.

Do not weaken, delete, or bypass persistence safety tests merely to obtain a passing release command.

Also run:

* acquisition tests for every touched or transitively affected source package;
* static historical artifact-integrity validation;
* receipt and manifest integrity checks;
* searches proving deleted legacy names have no surviving executable imports;
* searches proving no old registry or selector is referenced by production frontend code;
* JSON parsing for updated indexes and the cutover receipt;
* documentation integrity checks;
* `git diff --check`;
* final diff review;
* deleted-file review.

Report unrelated baseline failures separately. Do not broaden the milestone to fix them.

## Civic-integrity requirements

The cutover must preserve:

* exact-action rather than parent-measure interpretation;
* substantive versus procedural distinctions;
* limited-context distinctions;
* amendment versus final-passage distinctions;
* Present and Not Voting as resolved, non-directional states;
* missing-evidence and service-status distinctions;
* source and claim provenance;
* action accounting;
* typed source constraints;
* review routing boundaries;
* the rule that rendering cannot add analytical meaning;
* separation of semantic acceptance, human approval, benchmark status, production eligibility, publication, merge, deployment, and promotion.

Do not introduce:

* motive claims;
* ideology claims;
* corruption claims;
* character judgments;
* causality claims;
* predictions;
* rankings;
* candidate recommendations;
* voting recommendations.

## Stop conditions

Stop and report before destructive action if:

* a proposed deletion removes or weakens source acquisition;
* a proposed deletion removes the only production backup, export, rollback, reconciliation, or dependency-discovery path;
* a legacy test contains a useful invariant and no safe replacement can be created within the milestone;
* canonical accepted-reference validation requires changing an accepted reference;
* historical artifact integrity cannot be preserved without rewriting authoritative evidence;
* preserving the basic vote-evidence experience requires a new product or methodology decision;
* the application cannot build or start without materially expanding into a new frontend architecture;
* the task requires a database migration;
* the task requires production access;
* an unclassified path combines legacy editorial execution with acquisition or production-recovery responsibilities that cannot be safely separated within this milestone.

An obsolete replay test, obsolete builder dependency, or old frontend compatibility expectation is not by itself a stop condition.

Remove the obsolete dependency and transfer useful protection to the canonical, acquisition, provenance, or frozen-artifact layer.

## Delivery

Complete:

* discovery;
* dependency classification;
* test classification;
* coverage transfer;
* implementation;
* deliberate frontend fallback;
* tests;
* documentation;
* cutover receipt;
* final diff review.

Commit the changes and open a draft pull request.

Do not:

* merge;
* deploy;
* publish;
* promote;
* approve editorial artifacts;
* alter publication state;
* query or modify production;
* mark the pull request ready for review.

The final report must include:

* exact files deleted;
* exact files rewritten;
* every deleted or rewritten legacy test and its classification;
* replacement coverage for each transferred useful invariant;
* preserved acquisition boundaries;
* preserved historical-evidence boundaries;
* preserved production persistence and recovery boundaries;
* surviving frontend behavior;
* removed or deliberately unavailable routes;
* frontend build and startup results;
* canonical validation results;
* acquisition and artifact-integrity validation results;
* unresolved coupling, if any;
* confirmation that accepted corpora, receipts, dossiers, source evidence, and proof artifacts were preserved;
* confirmation that production, persistence, publication, deployment, and database state were untouched.
