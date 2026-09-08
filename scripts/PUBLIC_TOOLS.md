# Public package maintenance

`public_registry.json` records the ten packages' names, canonical descriptions, docs roots,
approved core and optional stack dependencies, and minimum GitHub topics. Existing topics
outside this minimum remain valid. The graph includes StochVolModels' core pricing dependency
on vanilla-option-pricers and its optional research integration with option-chain-analytics.

Run the stdlib-only contract tests with `python -m unittest discover -s scripts/tests`.
On the maintainer's Windows machine use `C:\Python\ArturSepp312\Scripts\python.exe`.
Never create a Python environment in a OneDrive checkout.

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

The scheduled workflow collects sources into fresh temporary clones and commits only its
JSON/Markdown report. Collection has read-only credentials; report writing is a separate job.
`python scripts/update_github_about.py` prints exact proposed command arguments without making
changes. Add `--apply` to update descriptions, homepages and the minimum topic set using an
authenticated `gh` session. This does not change wikis, Discussions or remove existing topics.

## Frequent publishing

Each package receives `.github/workflows/release.yml` and the two helpers generated from
`scripts/templates/`. Regenerate with `python scripts/generate_release_files.py --repos-root
/path/to/clones`; `--check` detects edited generated copies. Change the templates before
regenerating package files.

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

`python scripts/build_stats.py --reuse-existing-counts` regenerates the profile table using
its recorded metrics without any network requests. This is appropriate for a Docs-link or
layout-only change when a statistics provider is unavailable; it does not claim new counts.

Trusted Publishing setup is documented by [PyPI](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
The publisher action is pinned to [PyPA v1.14.2](https://github.com/pypa/gh-action-pypi-publish/commit/dc37677b2e1c63e2034f94d8a5b11f265b73ba33),
and artifact download to [actions/download-artifact v8.0.1](https://github.com/actions/download-artifact/commit/3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c).
