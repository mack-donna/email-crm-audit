#!/usr/bin/env bash
# One command for every repo check. Used by PROGRESS.md done_when, CI, and humans.
# Each check encodes a mistake that already shipped once (see CLAUDE.md "Known pitfalls").
#
# Setup (Python must match Render, currently 3.13):
#   uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements.txt "bandit>=1.9,<2"
# Override the interpreter with PYTHON=/path/to/python scripts/check.sh
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "No interpreter at $PY. Create .venv (see header) or set PYTHON=." >&2
  exit 1
fi

fail=0
step() { echo; echo "== $1"; }

step "requirements have upper bounds"
"$PY" scripts/check_requirements.py || fail=1

step "regression tests"
"$PY" -m pytest -q -p no:warnings tests/ || fail=1

step "bandit (medium+ severity)"
# Known false positives are documented in CLAUDE.md. The one medium (B104 in run.py)
# is suppressed inline with `# nosec B104`, so a new 0.0.0.0 bind elsewhere still fails.
"$PY" -m bandit -q -r . -ll \
  -x ./.venv,./venv,./email-audit-env,./vendor,./claude-code-tests,./startup-name-generator,./tests \
  || fail=1

echo
if [ "$fail" -ne 0 ]; then echo "CHECKS FAILED"; exit 1; fi
echo "ALL CHECKS PASSED"
