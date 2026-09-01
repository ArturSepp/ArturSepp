## Python environment (mandatory)

- Never create, use, or install packages into a Python virtual environment anywhere under `C:\Users\artur\OneDrive`.
- Keep this repository's environment outside OneDrive at `C:\Python\ArturSepp312`.
- Use `C:\Python\ArturSepp312\Scripts\python.exe` for Python, tests, linters, and package installation.
- If it is missing, create it with `py -3.12 -m venv C:\Python\ArturSepp312`.
- Never run plain `uv sync` or plain `uv run` from this checkout: uv otherwise creates `<repo>\.venv` even when uv was launched through a Python executable under `C:\Python`.
- If a uv project operation is required, first set `UV_PROJECT_ENVIRONMENT=C:\Python\ArturSepp312`; for pip-style operations prefer `uv pip ... --python C:\Python\ArturSepp312\Scripts\python.exe`.
- If any OneDrive-local environment already exists, do not use it; report it for removal.

# AGENTS.md

Guidance for AI coding agents working in the **ArturSepp** repository.
