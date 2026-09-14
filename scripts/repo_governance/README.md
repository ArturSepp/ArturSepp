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
repository-specific command.

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
