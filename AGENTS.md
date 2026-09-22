## Python environment (mandatory)

- Never create, use, or install packages into a Python virtual environment anywhere under `C:\Users\artur\OneDrive`.
- Keep this repository's environment outside OneDrive at `C:\Python\ArturSepp312`.
- Use `C:\Python\ArturSepp312\Scripts\python.exe` for Python, tests, linters, and package installation.
- If it is missing, create it with `py -3.12 -m venv C:\Python\ArturSepp312`.
- Never run plain `uv sync` or plain `uv run` from this checkout: uv otherwise creates `<repo>\.venv` even when uv was launched through a Python executable under `C:\Python`.
- If a uv project operation is required, first set `UV_PROJECT_ENVIRONMENT=C:\Python\ArturSepp312`; for pip-style operations prefer `uv pip ... --python C:\Python\ArturSepp312\Scripts\python.exe`.
- If any OneDrive-local environment already exists, do not use it; report it for removal.
- Run standard portfolio tasks through
  `& "$env:USERPROFILE\OneDrive\analytics\my_github\ArturSepp\scripts\repo_governance\Invoke-Repo.ps1" -Task verify`.
  Use `-Task check` or `-Task test` for a narrower run. The launcher selects this repository's
  external interpreter and routes generated state to C:.

# AGENTS.md

Guidance for AI coding agents working in the **ArturSepp** repository.

## OSS documentation standard

- The canonical authoring guide is [docs/documentation_standard.md](docs/documentation_standard.md).
  It owns shared article structure, attribution and dates, Markdown mathematics, references,
  figure provenance, navigation, and review requirements for the public Python stack.
- Each package's AGENTS.md links to this guide. QIS and OP retain supplements for their
  local tooling and numerical contracts. Change common rules here, preserve local exceptions,
  and keep the package links current.
- Keep shared documentation links outside the generated SHARED AGENT CORE blocks.
  Linking this guide does not certify migration or review of an existing package's pages.

## Agent-generated artifacts

All agent-generated roadmaps, execution plans, audits, reports, handoffs, and other working
outputs live under the repository-root `agents/` directory, which is local and ignored by Git.
Never create `ROADMAP_*.md`, `Claude outputs/`, `Codex outputs/`, or similar agent-output
artifacts at the repository root. Name feature roadmaps `agents/ROADMAP_<feature>.md`. An
execution request names the file and stage. A stage is complete when its stated verification
command passes; its out-of-scope list is binding.
