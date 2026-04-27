#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "[CI] Running local smoke checks"
echo "Hello, world!"

# Validate-submission equivalent: only changed submission files
BASE_REF=$(git rev-parse --verify HEAD~1 2>/dev/null || echo "")
if [[ -n "$BASE_REF" ]]; then
  CHANGED=$(git diff --name-only "$BASE_REF"...HEAD -- 'submissions/*/submission.yaml' 'submissions/*/Submission.yaml' || true)
else
  CHANGED=""
fi

echo "[VALIDATE] Changed submission files:"
echo "${CHANGED:-<none>}"

if [[ -n "$CHANGED" ]]; then
  python .github/scripts/validate_submission.py $CHANGED
else
  python .github/scripts/validate_submission.py
fi

# Zapier webhook local dry run (does not require secret)
PAYLOAD=$(python - <<'PY'
import json
print(json.dumps({
    "pr_title": "local-dry-run",
    "pr_url": "https://example.com/pr/0",
    "pr_number": 0,
    "author": "local",
    "repo": "local/repo",
}))
PY
)

echo "[WEBHOOK] Dry-run payload generated"
echo "$PAYLOAD" > reports/zapier_webhook_dry_run_payload.json

echo "All local workflow kickstart checks completed."
