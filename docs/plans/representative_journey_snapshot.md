# Representative journey snapshot package

## Intent and scope

Make the validated two-representative, four-case journey portable and testable
without its historical build chain. Package the exact reviewed HTML as an inert
local preview, with provenance, a standard-library check/export command and
focused integrity tests. Expected footprint: eight new files; targeted static
validation and an isolated-copy test, no dependencies or browser rerun.

Preserve the existing untracked v1 work and all frozen artifacts. No public app
route/import, semantic generator, editorial acceptance, canonical change,
production write, installation, commit, PR or deployment is authorized.
Interpretation principles remain applicable; presentation content is unchanged.

## Baseline and decision

- Branch: `codex/hr859-local-interpretation-preview`.
- HEAD: `b8b81a6acbbbdbaf3a67c1112a11c35fac04bd2c`.
- Tracked tree clean; eight existing untracked v1 files are outside this task.
- Reviewed HTML: `afb47ec78a48ec6b8a9c1aa9ac6fed7e7130a335211cdf512423965321cb1de3`.
- Independent PC Chromium receipt covers 24 journeys at 1440/390/320px with
  evidence navigation, back/forward and disclosure restoration; no recorded
  page errors or overflow. Reuse this receipt only for identical HTML bytes.
- An immutable snapshot avoids behavior changes and does not recreate an
  editorial generator. Its embedded JSON is the sole evidence-data copy.

## Sequence and definition of done

1. Add a separate package under `frontend/local-preview/representative-journey`.
2. Pin bytes, payload hashes and evidence bindings; retain the review receipt.
3. Add dependency-free verification/export and focused regression tests.
4. Verify a clean isolated copy without `.tmp`, history or `node_modules`.
5. Inspect changed files and reconcile against scope.

Done means exact reviewed output, all eight member/action bindings and sources
preserved, clean-copy operation proven, old work preserved, and public/editorial
integration gates documented. Export must verify before writing and refuse an
existing destination. The snapshot must be immune to Git newline conversion.

## Progress and validation

- Complete: five-file snapshot package, verifier/exporter, focused tests and this
  plan. Eight new normal-repository files; no existing files replaced.
- `python scripts/check_representative_journey_preview.py` passed: pinned HTML,
  three downloads, eight exact member/action bindings, 41 sources, 22 routes,
  CSP and the matching independent 24-journey browser receipt.
- `python -m unittest backend.tests.test_representative_journey_preview -v`:
  seven tests passed, including byte-identical exports, tamper rejection before
  writing, immutable review/evidence bindings and refusal to overwrite.
- Isolated-copy test copied only the five package files and verifier into a
  clean directory with spaces. The CLI ran with Python isolated mode from an
  unrelated working directory, exported identical HTML/downloads, and rejected
  corruption with Python assertions disabled. No `.tmp`, history, original
  review location, `node_modules` or other repository file was available there.
- Git confirmed `text: unset` for the HTML and browser receipt; their exact bytes
  survive newline normalization (raw and clean-filter Git hashes matched).
  Generated artifacts and code/diff were inspected. Preservation checks verified
  all eight prior untracked files, 59 frozen entries and 322 older protected files.
- Initial filesystem tests failed with `WinError 5: Access is denied` beneath
  Windows system Temp (`representative-journey-*`) before copying package files;
  cleanup there was also denied. Those paths were left untouched. Tests now use
  inherited permissions in the repository's permitted `backend/.pytest_tmp`
  scratch area, with bounded cleanup. This is test scratch, not a package input.
- Existing pytest-cache directory permission warnings are unrelated; not retried.
- Independent native package review passed on November 6, 2026, with no blocking
  defects. The reviewer reran all seven tests and the CLI, separately verified
  isolated-copy export without history/dependencies/cwd assumptions, and confirmed
  unchanged reviewed HTML, no public-runtime references or semantic/member changes,
  exact-byte Git attributes, validation before export, refusal to overwrite and
  active integrity checks under Python optimization. No files were modified by
  the reviewer. This status reconciliation changes only this plan and the README.

## Limits and later gate

This is packaging, not production integration or editorial acceptance. Any
future public presentation requires a separately authorized IR-native integration
milestone and applicable editorial review. Local package review is complete.
Library delivery remains blocked separately by the reported selected-folder 403;
no transfer workaround is authorized. No new browser/cloud rendering is needed
for unchanged bytes. No production writes occurred; rollback is removal of only
these newly introduced package/tool/test/plan files, leaving prior work intact.

## Final reconciliation

The local packaging definition of done is satisfied: output remains
`afb47ec78a48ec6b8a9c1aa9ac6fed7e7130a335211cdf512423965321cb1de3`,
with no semantic, public runtime or UI behavior change. The prior browser result
is reused by checksum; no browser was launched. No production writes occurred.
Independent package review passed with no blocking defects. Public integration still requires the
separate IR-native/editorial milestone; artifact delivery remains a separate
unresolved Library gate. No commit, push, PR, merge or deployment was performed.
