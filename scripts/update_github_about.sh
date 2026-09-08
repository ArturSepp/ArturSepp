#!/usr/bin/env bash
# Dry-run by default; --apply uses the authenticated gh session.
set -euo pipefail
exec "${PYTHON:-python}" "$(dirname "$0")/update_github_about.py" "$@"
