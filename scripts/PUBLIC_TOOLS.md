# Public package maintenance

`public_registry.json` records the ten packages' names, canonical descriptions, docs roots,
approved core and optional stack dependencies, and minimum GitHub topics. Existing topics
outside this minimum remain valid. The graph includes StochVolModels' core pricing dependency
on vanilla-option-pricers and its optional research integration with option-chain-analytics.

Run the stdlib-only contract tests with `python -m unittest discover -s scripts/tests`.
On the maintainer's Windows machine use `C:\Python\ArturSepp312\Scripts\python.exe`.
Never create a Python environment in a OneDrive checkout.

The Windows portfolio-wide command interface is documented in
[`repo_governance/README.md`](repo_governance/README.md). Its registry covers the public profile,
all ten public packages, and the three private checkouts while keeping public package metadata
in `public_registry.json`. It provides uniform `check`, `test`, and `verify` tasks, C-local
generated-state setup, agent-policy validation, and LaTeX builds.

`python scripts/conformance.py --repos-root /path/to/clones --output /path/to/report`
checks existing local sources without network access. `--online` adds public GitHub and PyPI
observations; `--fail-on-drift` gives a nonzero exit on known defects. Unavailable APIs and
missing sources are reported as unknown, not passing. Historical release checks cover every
PyPI version with artifacts uploaded since 2026-08-01. The source version may be ahead of PyPI;
GitHub Release pages are optional. This initial checker covers metadata, the approved graph,
import bans, tracked hygiene, action pins and tag/version consistency. It does not certify
historical artifact provenance, numerical results or every README/docs convention.
The reviewed `agent_core_manifest.json` hashes the entire generated agent block. Release
files are compared with their reviewed templates, so edits retaining a current stamp fail.
Historical provenance gaps stay visible as `known-gap`, independently of new missing-tag failures.

Regenerate an existing package's `.github/stack-policy.json` from the registry with
`python scripts/generate_stack_policy.py --repos-root /path/to/checkouts --package factorlasso`.
Repeat `--package` to select another package; selection is mandatory and no other checkout is
changed. Add `--check` to verify the generated policy without writing. The generator does not
create policies for repositories that use a different boundary-check interface.

### Recorded runtime licence review

The focused `license_policy.py` assertion checks a saved **runtime-only** `pip inspect`
inventory against an independently reviewed package/version record and that installation's
complete notice files and selected native-binary hashes. The review supplies exact licence
metadata, full notice paths/digests, interpreted terms, platform and qualifications. Capture
the inventory before adding test tools; only seeded `pip` is excluded. This is the bounded
assertion used for the MIT transition, not a general SPDX scanner or an all-platform audit.

```powershell
& C:\Python\ArturSepp312\Scripts\python.exe scripts/license_policy.py `
  --inspect C:\evidence\base-inspect.json --review C:\evidence\base-reviewed.json `
  --site C:\external-env\Lib\site-packages --output C:\evidence\licence-result.json
```

Use the actual external evidence/environment paths. The saved inventory and installed
notices must belong to the same recorded resolution. A pass establishes that record, not
the state of later test-tool installations or every version allowed by dependency ranges.
Unknown packages, versions, licence metadata, unresolved reviews and changed/missing full
notices fail. A plain mandatory GPL/AGPL/LGPL identity fails; a manually reviewed genuine
alternative or compiler-runtime exception is not rejected by a GPL substring search.
The independent review remains responsible for interpreting those terms, including
compound expressions, source rights and unrecorded bundled components.

MIT applies to cleared first-party source. The reviewed Windows numerical runtime retains
NumPy/SciPy's `GPL-3.0-or-later WITH GCC-exception-3.1`, Microsoft redistributable terms,
Numba's NVIDIA header terms, and font/data attribution. Complete supplemental OpenBLAS
notices accompany affected stack packages. No entirely MIT, literally GPL-free, or wholly
permissive binary environment is claimed; optional solver/provider installations are
separate reviews. Full notices and applicable conditions remain required.

The existing conformance entry point accepts the same bounded review using
`--license-inspect`, `--license-review`, and `--license-site` together. It writes a separate
`runtime_license` result and preserves its qualifications; without evidence this result is
`unknown`. An explicitly requested runtime failure exits nonzero even without
`--fail-on-drift`. Existing eleven-package metadata/backlog findings remain separate and
are not cleared by this one-runtime pass. Run its controlled failure/restoration tests with
`python -m unittest discover -s scripts/tests -p test_license_policy.py`.

The scheduled workflow collects sources into fresh temporary clones and commits only its
JSON/Markdown report. Collection has read-only credentials; report writing is a separate job.
`python scripts/update_github_about.py` prints exact proposed command arguments without making
changes. Add `--apply` to update descriptions, homepages and the minimum topic set using an
authenticated `gh` session. This does not change wikis, Discussions or remove existing topics.

## Live sitemap verification

`verify_sitemaps.py` checks published XML using Python's standard library and the system
`curl` executable (Windows curl.exe, or curl on Linux/macOS). It starts a new curl process for
each exact URL, ignores curlrc, uses no browser state or cookie jar, and does not add query
parameters or follow redirects. It records status, selected HTTP/cache/routing headers and
SHA-256 hashes without retaining cookie/credential headers. Temporary downloads use the
system temporary directory; apply the mandatory C-local setup on the Windows maintainer host.

```console
python scripts/verify_sitemaps.py --site https://bloombergfetch.readthedocs.io --site https://privateassets.readthedocs.io --site https://vanillaoptionpricers.readthedocs.io --version latest --check-pages
```

Add `--output /path/to/external/sitemaps.json` to save evidence instead of printing JSON.
The required `--version` selects the intended default/indexed channel; QIS uses `--version stable`.
With exactly one site, `--expected-sitemap /path/to/build/html/sitemap.xml` additionally checks
the actual locally built inventory. The tool accepts page URL sets, not sitemap indexes.
A local fixture server may use loopback HTTP; deployed sites require an HTTPS origin.

The root and version inventories must agree, be nonempty, have no duplicates or homepage
index.html alias, and remain inside the selected channel. Nested api/index.html is preserved.
XML ordering, whitespace, body hashes and ETags may differ without an inventory mismatch.
`--check-pages` verifies every listed page's canonical, meta/HTTP robots and meta refresh;
without it the report explicitly says page checks were not requested. The default page
limit is 1,000 per site; exceeding `--max-pages` is unverified, not a sampled pass.

Exit codes: **0 verified**, **1 observed mismatch**, **2 unverified**. A mismatch describes the
received content; it does not identify a stale origin or cache. Non-200 responses, challenges,
transport errors or incomplete checks cannot pass. Requests stop immediately on HTTP 429 and
record Retry-After when supplied. The default interval is one second; do not bypass rate limits.
Missing curl is unverified. This tool never purges caches, changes hosting settings, triggers
builds or submits anything to Google. Verify the deployed source/build separately.

Run its offline regressions with `python -m unittest discover -s scripts/tests -p test_verify_sitemaps.py`.
The local HTTP fixture checks that repeated requests observe server changes even when responses
advertise a four-hour cache lifetime; it needs system curl and uses no external service.
The existing required workflow discovers these tests without running the online command.

### Historical URLs and permanent redirects

Current sitemap checks do not cover removed pages that Google or external sites still link to.
Keep a reviewed redirect inventory in the owning repository and add `--redirect-manifest` for
one selected site/channel. The version-1 JSON identifies `site` and `redirects`; each rule has
`from_url` (page-relative, starting with `/`), absolute HTTPS `to_url`, `redirect_type: "page"`,
`http_status: 301`, `enabled: true`, and `force: false`. Read the Docs applies these rules only
when a page is missing, preserving archived pages that still exist. Apply the reviewed rules
in the project's Redirects settings; the checker only reads them and never changes hosting.

```console
python scripts/verify_sitemaps.py --site https://optimalportfolios.readthedocs.io --version latest --redirect-manifest /path/to/OptimalPortfolios/tools/docs_redirects.json --output /external/evidence/op-redirects.json
```

The checker requires the exact permanent Location or an existing self-canonical page, then
verifies the replacement's HTTP 200, canonical, robots metadata and any destination fragment.
Destinations shared by multiple rules are downloaded once within that run. Temporary redirects,
redirect chains, 404s and missing anchors are observed mismatches; blocked access remains
unverified and a 429 stops requests. Add `--check-pages` to check the sitemap's page inventory
in the same run. Read the Docs' [redirect behavior](https://docs.readthedocs.com/platform/stable/user-defined-redirects.html)
is separate from repository build validation; verify the live rules after applying them.

### Scheduled documentation monitor

`monitor_documentation.py` checks all packages in `public_registry.json` using independent
HTTP requests. `documentation_monitor_seed.json` records the reviewed channel policy and
bootstrap history: 928 preferred pages and 98 legacy paths from the 2026-10-27 audit. QIS
uses `stable`; the other packages use `latest`. Legacy paths are checked on both active
`latest` and `stable` channels. The seed is historical evidence, not a fixed expected sitemap
size. Newly published sitemap URLs are learned and retained even after they disappear.
Reviewed redirect manifests are fetched from each repository's published `main`, so local
uncommitted redirect drafts cannot change the operational result.

On the Windows maintainer host, apply the mandatory setup in the same PowerShell session:

```powershell
. .\scripts\repo_governance\Enter-AgentRepo.ps1 -RepoPath (Get-Location).Path -RepositoriesRoot (Split-Path (Get-Location).Path)
& C:\Python\ArturSepp312\Scripts\python.exe scripts/monitor_documentation.py `
  --state-dir (Join-Path $env:AGENT_LOCAL_ROOT 'state\documentation-monitor')
```

Keep the state directory on C-local storage. `state.json` holds the append-only URL ledger,
pending/confirmed findings and notification deduplication; timestamped `report-*.json` and
`latest.json` hold response hashes, selected headers, observed defects and notification deltas.
Do not delete state merely to silence an alert. Review the seed/channel policy when onboarding
a package or deliberately retiring a channel. This covers audited or observed URLs, not every
hypothetical path or pages added and removed between runs. It is not a general external-link
crawler and does not establish Google's indexing state.

Two definitive failures at least one hour apart confirm a new issue. Unchanged confirmed
issues remain silent; a verified recovery produces one recovery event. Access blocks, throttles,
5xx, challenges and transport failures are **unverified**: they reset pending confirmation and
cannot clear an active finding. Three consecutive incomplete runs produce one separate
monitoring-unavailable warning, with one recovery event when access returns. A global 429 stops
new requests; at most two package workers share one-second per-host pacing and an in-run cache.
An unavailable sitemap stops page probing for that package. Missing optional redirect manifests
are expected; previously required manifests that become unavailable remain unverified.

The standalone [OSS documentation monitor](../.github/workflows/documentation-monitor.yml)
runs on GitHub-hosted runners daily at **08:17 Europe/Zurich**, including daylight-saving changes.
It has only `schedule` and `workflow_dispatch` triggers, with no push, pull-request or reusable
workflow trigger. It runs while the maintainer's computer is off. The former local Codex
schedule is retired after the first hosted run succeeds. To run it manually, use the workflow's
**Run workflow** button on `main`, or `gh workflow run documentation-monitor.yml --ref main`.

`scripts/documentation_monitor_actions.py` restores the URL ledger and alert state from
`documentation-monitor.json` on the dedicated `automation/documentation-monitor` branch.
The local command above remains useful for manual diagnostics; its state directory is separate
from the hosted state. Initial hosted setup transfers the existing local history once. A missing
or unreadable remote snapshot is an infrastructure failure, never permission to reset history.
State updates use the previous blob SHA and fail on conflicts. Full HTTP evidence and run
summaries are uploaded as 30-day Actions artifacts; durable confirmation state does not depend
on expiring artifacts or evictable caches. Do not merge the state branch into `main`.

New confirmed failures, verified recoveries and sustained monitoring warnings are reported
in one tracking issue assigned to **ArturSepp**, with an explicit mention and the evidence-run
link. The issue is created only when an event needs reporting, reopened for a new event, and
closed after all confirmed issues and monitoring gaps recover. Unchanged findings produce no
comments. Delivery follows GitHub notification preferences; no email credentials or custom
secrets are required. Pending events are committed before notification, and unique event
markers prevent duplicate comments after an interrupted acknowledgment. Persist a creation
intent before posting a new issue. If that issue is not yet discoverable after an interrupted
write, defer notification delivery rather than create a replacement. GitHub API reads request
revalidation; an absent listing never proves that a previous creation failed. A genuinely
ambiguous failed creation may require maintainer reconciliation of the pending intent.
Partial GitHub API failures fail only this independent workflow and leave pending delivery
recoverable.

The checking job has read-only contents access. Only the separate record-and-notify job gets
`contents: write` and `issues: write` with the repository's `GITHUB_TOKEN`; it changes only the
automation state branch and its tracking issue. Workflow concurrency serializes scheduled and
manual runs. Checkouts do not persist credentials, third-party actions are pinned, and no
pull-request source or documentation HTML is executed. The workflow changes no redirects,
hosting or search-engine settings. The monitor emits `notification_required` and the `alerts`,
`recoveries`, `monitor_warnings` and `monitor_recoveries` deltas for this delivery adapter.

GitHub can delay scheduled runs and can disable schedules after 60 days without repository
activity; review the workflow's enabled status when returning to an inactive repository. See
[GitHub's scheduled-workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Operational network findings always exit **0**, including confirmed failures; invalid
configuration or inability to save evidence exits **2** as a monitor error. A pre-existing lock
skips requests without claiming a pass; inspect its PID before removing an abandoned lock.

Keep this online command outside required push/PR checks and pre-commit hooks. The existing
strict manual verifier retains its 0/1/2 outcomes. CI discovers only deterministic offline
monitor tests: `python -m unittest discover -s scripts/tests -p "test*monitor*.py"`.

## Frequent publishing

Each package receives `.github/workflows/release.yml` and the two helpers generated from
`scripts/templates/`. Regenerate with `python scripts/generate_release_files.py --repos-root
/path/to/clones`; `--check` detects edited generated copies. Change the templates before
regenerating package files.

For a scoped workflow change, use `python scripts/generate_release_files.py --repos-root
/path/to/clones --package optimalportfolios --workflow-only`; add `--check` to verify
the selected output. Package-specific release helpers and every other repository remain
untouched. OP's reviewed registry profile retains its Europe/Zurich timezone and checks the
explicit `[riskbudget]` backend after the base tests. That lane requires a nonempty result
with no failed, errored or skipped cases before the validation job can permit publication.

After the usual release metadata commit has reached `origin/main`, run the package's
`python .github/scripts/publish_tag.py vX.Y.Z --push`. Omitting `--push` is a local dry run.
Only that tag is pushed. The workflow tests the tagged source, builds the tagged docs, builds
one sdist and its wheel, checks package metadata and imports the wheel in a clean environment.
The same built files flow to the separate PyPI publishing job. No GitHub Release page or
manual approval is required for each normal upload.

One-time setup for each PyPI project: add a GitHub Trusted Publisher for owner `ArturSepp`,
the exact repository, workflow `release.yml`, environment `pypi`. Configure the GitHub `pypi`
environment without mandatory reviewers if unattended frequent publishing is desired.
Allow environment deployments from `main` and tags matching `v*`; protect main and release
tags against unauthorized changes. Dispatch the workflow from `main` only. A pushed tag must
still resolve to the triggering push commit, and every selected tag must belong to main history. Existing
manual publishing credentials remain a separate supported route; this workflow does not
claim to make every other publisher impossible or revoke any credentials.

Workflow dispatch accepts an existing named tag. It never chooses a version or moves a tag.
Existing PyPI artifacts must match the rebuilt filename and SHA-256 exactly, otherwise the
workflow stops. A fully matching existing version is verified and skipped. Tag backfills
never append artifacts to an existing version. To finish a partial failed upload, explicitly
select `retry_existing`; every already uploaded file must still match. Blind skip-existing is
disabled. A transient PyPI API failure blocks the upload instead of being treated as absence.
Build timestamps are anchored to the tag commit through `SOURCE_DATE_EPOCH`; dependency and
build-backend changes can still make a reconstruction differ, in which case use the retained
original artifacts and investigate rather than overriding the mismatch.

An optional `github_release` dispatch input creates a GitHub Release page after validation and
successful publication (or a digest-matched existing version). Its default is false. Creating
a release page later does not require a new package upload.

The public registry and release templates are reviewed exports. The private portfolio master
documents and project-knowledge copies remain outside this public repository.

The helper accepts bounded release, prerelease, postrelease and `.devN` tags, including
`v1.2.3.dev1`. CFF records the intended release date; the immutable PyPI upload timestamp is
the independent publication evidence. Artifact checks include SPDX license expression,
actual license files inside both archives, Python requirements and core dependencies.
Archives must contain the source package and exclude local data runners, IDE files, caches,
and environments. BloombergFetch's reviewed registry variance installs `blpapi` from
Bloomberg's public SDK index after each environment sync and in the isolated wheel check;
the tests remain terminal-free.
StochVolModels preserves its CI platform split: tagged fast tests run on Linux, and the
Windows Python 3.12 numerical regression job checks the same validated commit with its
locked test dependencies. Both must pass before uploading or creating an optional release page.

`python scripts/build_stats.py` regenerates the profile table without network requests.
GitHub and Pepy badges supply current counts when the README is viewed. Run
`python scripts/build_stats.py --check` to verify that the committed table matches its
package metadata.

Trusted Publishing setup is documented by [PyPI](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
The publisher action is pinned to [PyPA v1.14.2](https://github.com/pypa/gh-action-pypi-publish/commit/dc37677b2e1c63e2034f94d8a5b11f265b73ba33),
and artifact download to [actions/download-artifact v8.0.1](https://github.com/actions/download-artifact/commit/3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c).

The `factormodels` registry entry enables its scoped `release_navigation_check`.
The release producer runs `tools/check_navigation_refs.py --require-current-source`
after exact tag checkout and before tests/builds. The package records its reviewed
navigation ref and any individually explained immutable evidence links; the guard
preserves historical `/commit/` links and other repositories. Preparation mode can
check a recorded prepublication ref, while release mode requires that ref to resolve
to the clean checked-out commit. Other package workflow emissions are unchanged.
