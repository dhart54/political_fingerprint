# Representative journey — immutable local preview

From the repository root, with Python 3.11 or newer:

```powershell
python scripts/check_representative_journey_preview.py
```

Open `preview.html` in this directory to use the standalone preview. No server,
package installation, `.tmp` files, historical builders or frontend dependencies
are required. JavaScript handles local navigation; official source links require
connectivity. The HTML includes its three evidence downloads.

For a verified copy and extracted JSON downloads, add `--export-dir <new-folder>`
to the command. The destination must not already exist. The command validates
everything before writing, preserves exact HTML/download bytes, and performs no
network requests. Focused tests: `python -m unittest backend.tests.test_representative_journey_preview`.

`manifest.json` pins the reviewed artifact, embedded payloads, exact actions and
member records. `browser-review.json` is the unchanged independent PC Chromium
result for the same HTML hash: 24 journeys across both representatives, four
cases and widths 1440/390/320px. The prior harness checked evidence navigation,
back/forward and disclosure restoration. The receipt records no page errors or
overflow. Packaging reuses that result; it does not claim a new browser run or
human comprehension test. The local `.gitattributes` preserves reviewed bytes.

The snapshot is intentionally immutable. There is no prose generator or adapter
to the public frontend. Changes require a separately reviewed replacement
snapshot, synchronized manifest/checker pins and appropriate content/rendered
validation. Never refresh hashes merely to make an unexplained change pass.
The existing `interpretation-v1` work is separate and has not been replaced.

Public integration requires a separately authorized **IR-native presentation
milestone** and the applicable editorial review/acceptance gates. Local UI and
content review do not confer canonical acceptance, publication eligibility or
approval to import this candidate into public routes. No app route imports this
package. Pipeline presentation remains a candidate. Source navigation retains
nine topic gaps and seven printed-page gaps, using the reviewed section/text
guidance; no new source verification is claimed.

Independent native package review passed on November 6, 2026, with no blocking
defects. It confirmed the seven tests and CLI, a separate isolated-copy export,
unchanged reviewed HTML and member/semantic content, no public-runtime
references, exact-byte Git protection, validation before export, refusal to
overwrite, and integrity checks with Python optimization enabled. The reviewer
did not modify files. This completes local package review only.

Artifact delivery is a separate gate:
the reported Library selected-folder 403 is not resolved by local export. No
upload, download or alternate transfer route is part of this package.
