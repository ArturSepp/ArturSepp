# Portfolio repository workflow

This directory is the versioned control plane for local work across the 14 repositories in the
adjacent `my_github` folder. It provides one registry and one command interface without erasing
repository-specific test, lint, numerical, or release constraints.

The local execution registry is `portfolio_registry.json`. Public package identity, metadata,
dependency edges, and release policy remain in `../public_registry.json`; the policy check proves
that the ten public-package entries in both registries agree.

From any registered checkout:

```powershell
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1" -Task check
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1" -Task test
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1" -Task verify
```

Use `-Repo <name>` from elsewhere, `-All` for a sequential portfolio run, and `-DryRun` to inspect
the exact external-interpreter commands. `verify` runs the registered `check`, `test`, and any
additional repository verification steps. Unsupported phases are explicit skips; currently only
SigmaStrats lacks an automated test interface.

`Enter-AgentRepo.ps1` selects `C:\Python\<environment>\Scripts\python.exe`, rejects environments
inside OneDrive, and routes Python, pytest, Ruff, mypy, coverage, build, output, and temporary state
below `%LOCALAPPDATA%\AgentWork\<machine>\<repository>`. It can also be dot-sourced before a manual
repository-specific command. It sets `OPTIMALPORTFOLIOS_OUTPUT_PATH` to that directory's
`outputs` folder, so `optimalportfolios.local_path.get_output_path()` writes there and not into
the OneDrive checkout.

Run the governance checks with:

```powershell
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Test-PortfolioPolicy.ps1"
& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Update-AgentCoreManifest.ps1"
```

The first command verifies registry consistency, external environments, agent pointers, ignored
artifact placement across each repository tree, declared task paths, and the reviewed public
agent-core hashes. Repository-specific retained documentation or output trees are explicit
`artifact_policy.roadmap_exclusions` entries in the registry. The second command is read-only by
default; `-Write` regenerates the manifest after a deliberate shared-core update.

Build LaTeX through `Build-AgentLatex.ps1 -MainTex <path>`. Auxiliary files and the default PDF
stay on C:. `-Publish` copies the final PDF beside the source and refuses to overwrite it;
`-ForcePublish` is the explicit overwrite operation.

## Retained roadmap exceptions

The six exact OP file paths in artifact_policy.roadmap_exclusions preserve existing
workspace contracts reviewed on 15 October 2026:

- papers/equity_factors/ROADMAP_equity_factors.md is the execution contract explicitly
  required at that location by the study's local AGENTS.md.
- The two WBS presentations/ roadmaps are referenced by the existing deck. Its local
  AGENTS.md protects the presentation currently being edited by the user.
- Three matching WBS roadmaps in the dated 27 and 28 September draft archives remain with
  their self-contained historical decks, as required by papers/AGENTS.md.

These are file-specific retention exceptions, not permission for new agent outputs in
those folders. New paper working records belong in each paper's agents/. The policy
regression test exercises the actual registry and rejects neighbouring new roadmaps,
new draft folders and unrelated papers. No publication or ignore-rule exception is added.

The two exact FactorLasso exclusions under
papers/exposure_budget_floor_2026/submission/Downloads retain imported roadmap source
files in a self-contained submission bundle. The paper's local AGENTS.md requires the
preserved inputs and packages to remain self-contained and its archived records to remain
unchanged. These imported documents identify a different canonical working location;
they are retained source material, not new execution records for that paper.
Their bytes are preserved. The registry regression rejects neighbouring new roadmaps
and an identically named pointer in another folder. New paper working records still
belong in agents/; this adds no public tracking or distribution permission.
