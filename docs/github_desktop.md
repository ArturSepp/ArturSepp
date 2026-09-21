# GitHub Desktop workflow for the OSS stack

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Use GitHub Desktop to save work normally. Automatic local checks give early feedback;
the full required checks run when you choose to open a pull request.
This guide applies to the ten libraries in the [package directory](documentation_standard.md#package-directory),
including [qis](https://github.com/ArturSepp/QuantInvestStrats)
([software citation](https://github.com/ArturSepp/QuantInvestStrats/blob/main/CITATION.cff)).

## Daily use

1. Fetch the latest `main` in Desktop. Commit there directly, or create a working branch when you want a pull request.
2. Select the files or lines you intend to commit. Press **Commit** normally.
3. If the check fails, read its file/line and repair message, fix the issue, and select the
   repaired contents again. The check does not change or select files for you.
4. Push your commit. If you used a working branch, open a pull request and merge after **Required checks** passes.

Saving a local commit does not itself run GitHub Actions. Direct pushes to `main` do not
launch **Required checks**; pull requests and manual dispatches do. The maintainer can merge
their own pull requests; a second person's approval is not required.

GitHub Desktop can bypass local hooks for a work-in-progress commit. This does not bypass
the remote required checks on a pull request. A direct `main` push is not CI-gated, so run
the longer checks explicitly before publishing changes that warrant them.
[Desktop hook documentation](https://docs.github.com/en/desktop/making-changes-in-a-branch/working-with-git-hooks-in-github-desktop)

## Install once on each Windows host

After fetching the reviewed tooling into the shared repository and packages, run:

```powershell
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Install-CommitHooks.ps1" -All -SetupTools
```

The installer preserves existing custom hooks by refusing to overwrite them. It enables the
tracked `.githooks` entry point in each public package, installs pinned development tools in
`C:\Python\ArturSepp312`, and verifies the downloaded workflow validator's checksum.
The repository's configured external Python environment must already exist. No environment,
cache, or temporary source export is created below OneDrive. Git metadata stays in OneDrive.

The hook starts a noninteractive PowerShell session and configures its environment itself.
There is no need to run `Enter-AgentRepo.ps1` manually before a Desktop commit.
Hook configuration is local to a checkout. Check it after installing another computer or
creating a new clone. Do not use two computers concurrently against the OneDrive checkout.

## Understand a failed check

The hook exports the exact Git index: a selected line is checked even if an unstaged edit
already repairs it in the working file. Conversely, unrelated unselected work is not included.
It checks affected syntax, workflow definitions, the package's lint rules, citation/version
agreement, lock consistency and applicable documentation/generated-file contracts.

Read the displayed command and log path. Logs live under
`%LOCALAPPDATA%\AgentWork\<computer>\<repository>\checks\logs`.
Missing tools or an offline dependency-cache miss require setup; a commit hook never installs
dependencies or silently rewrites a lockfile. Existing numerical and coverage gates remain in CI.

To preview coupled citation-version repairs without changing files:

```powershell
& "C:\Python\ArturSepp312\Scripts\python.exe" "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\sync_version_metadata.py" --repo .
```

Add `--write` only after reviewing that diff, then select the changed files in Desktop.
The tool takes the version from `pyproject.toml`; it does not bump it or change release dates.

For coupled files, explicitly select the complete change: for example the package version,
`CITATION.cff`, and the README software citation. Use existing package producers for generated
API lists and notebook mirrors; inspect their diff before selecting it. Never bypass a known
scientific failure merely to obtain a green status.

## Run longer checks explicitly

From a registered checkout, the shared launcher supports:

```powershell
$launcher = "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1"
& $launcher -Task doctor
& $launcher -Task preflight
& $launcher -Task docs
& $launcher -Task ci
```

The new profiles check selected contents by default. Use `-Revision HEAD -Base HEAD^` to
check the latest committed change. `docs` builds strict HTML and applicable doctests; `ci`
adds the local package test command. The profile explicitly lists checks requiring the remote
environment, such as the OS/Python matrix, clean-wheel installs and coverage jobs. It does not
claim that a Windows run substitutes for all of those jobs.

The established `check`, `test`, and `verify` commands retain their working-directory
behaviour. Use the new profiles when an exact selected or committed snapshot is required.
The same versioned documentation commands and preflight checker run in GitHub Actions.

## Remote checks and maintenance

**Required checks** runs on pull requests, including documentation-only changes, and can be
started manually. It requires every applicable component to succeed; a cancelled or
unexpectedly skipped component fails the gate. Security auditing is required when dependency
inputs change. Direct pushes to `main` do not run this workflow.

Introduced references are checked on each pull request: confirmed 404/410 responses or missing
static anchors fail the gate. Rate limits, timeouts and server errors are recorded as unavailable
evidence for follow-up, rather than treated as proof of a defective edit.

Broad external-link checks and live dependency compatibility run separately on schedules.
A rate limit, website outage or new security advisory can therefore be identified as
maintenance work. Genuine broken references and vulnerabilities must still be repaired.
Strict HTML builds, tests, package boundaries, coverage and scientific regressions stay enforced.
Production-source changes also run applicable consumer import checks from pinned consumer commits.
Each consumer uses its reviewed lockfile, then installs the proposed package and verifies dependency
consistency and import compatibility. Ordinary prose changes skip this conditional check.

The shared repository publishes automatic statistics and conformance reports on the
[`automation/reports` branch](https://github.com/ArturSepp/ArturSepp/tree/automation/reports).
Scheduled bots use their own branches. Pull requests remain available for changes needing a
full remote validation pass before they reach `main`.

## Tooling maintenance

`scripts/repo_governance/oss_checks.py` is the canonical checker. Package copies are deliberately
versioned, with `.github/oss-checks.json` recording local conventions and the original workflow
check inventory. Update the canonical source and package copies together, test the change,
and review the adoption audit. A future tool release must be reviewed before changing its pin.

To disable only the managed local hook, run the installer with `-Repo <repository> -Uninstall`.
This leaves tracked files and remote workflow settings intact. Integrate third-party hooks
explicitly instead of replacing an existing `core.hooksPath`.
