# Exact CI evolution guard correction141

Hosted run39651713141 at exact feature head `a988dd87` exposed an in-scope
regression: the approved `.gitattributes` path additions broke two historical
whole-push-block substring assertions, failing the M14E/F/G jobs. The failure is
not classified as a hosted baseline issue. [Evidence](failure_evidence.json)
separates their exact feature checkouts from the successful synthetic-merge job.

The corrected helper allows exactly the same header or the exact two approved
attribute-path additions. It rejects every other header/path/event/branch change
and any new change to prior jobs. The already accepted main receipt-job extension
is preserved only if the supplied baseline authenticates as pinned main's exact
workflow blob and retains the original job bytes. That pin cannot excuse a new
runner, permission, checkout, command or appended-step change. New jobs remain
possible under the established historical test contract.

The actual workflow is separately required to contain both attribute filters.
Unexpected top-level sections after `jobs:` and duplicate job IDs also fail.
This includes the actual a988 workflow plus a new job followed by root-level
write permissions; on/env/concurrency/defaults/duplicate-jobs probes are covered.

A focused test module runs in the existing compatibility step. No product code,
accepted payload, wording, source pool, schema, provenance sidecar or authority
flag changes. [Validation](validation_results.json) records42 passing focused
tests and24 negative cases, plus the distinct Windows-only frozen-byte limitation
of a broader local attempt. [Exact byte evidence](local_windows_byte_check.json) proves that reviewed, a988,
HEAD, index and current-generator bytes match; the Windows worktree differs only
by437 CRLF pairs. The historical artifact was left untouched.

Independent review and exact successor hosted checks remain required before
completion. This correction grants no PR merge, editorial acceptance, H.R.859
admission, publication, deployment, main update or production authority.
