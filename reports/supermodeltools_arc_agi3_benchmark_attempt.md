# Supermodeltools setup + context bomb + scorecard output

Date (UTC): 2026-04-27

## Requested setup steps

### 0) Persist `SUPERMODEL_API_KEY` and reload shell
- Ran:
  - `echo 'export SUPERMODEL_API_KEY=***' >> ~/.bashrc && source ~/.bashrc`
- Verified:
  - `bash -ic 'echo SUPERMODEL_API_KEY_SET:${SUPERMODEL_API_KEY:+yes}'`
  - Output: `SUPERMODEL_API_KEY_SET:yes`
- Status: **Completed successfully**.

### 1) MCP Server — codebase graph queries
- Ran:
  - `claude mcp add supermodel --env SUPERMODEL_API_KEY=*** -- npx -y @supermodeltools/mcp-server`
- Output:
  - `Added stdio MCP server supermodel ...`
- Status: **Completed successfully**.

### 2) Uncompact — context recovery after compaction
- Ran:
  - `npm install -g uncompact --foreground-scripts`
- Output:
  - npm install completed, but postinstall release fetch hit `ENETUNREACH`.
- Workaround:
  - Manually downloaded `uncompact_linux_amd64.tar.gz` from GitHub Releases and installed binary to npm package bin path.
- Verification:
  - `uncompact dry-run --mode local --max-tokens 400`
- Status: **Completed successfully (with manual binary workaround)**.

## Supermodeltools memory tool output (context bomb)

Generated via:
- `uncompact dry-run --mode local --max-tokens 400`

Metadata output:
```text
[dry-run] local mode — no API key required
[dry-run] no cache — building from local analysis (results will NOT be cached)
[dry-run] 328 tokens (max: 400)
--- context bomb preview ---
```

Context bomb excerpt:
```markdown
# Uncompact Context — ARC-AGI-Community-Leaderboard

> Injected by Uncompact at 2026-04-27 22:50:03 UTC | local mode (set SUPERMODEL_API_KEY for AI-powered features)
**Language:** Python · **Files:** 17 · **Functions:** 0

## Critical Files
1. main.py
2. uv.lock
```

## Scorecard output

Opened a local competition-mode scorecard using the ARC toolkit scorecard manager and captured the returned card JSON.

Command (Python):
- Initialize `arc_agi.Arcade(operation_mode=OFFLINE)`
- `scorecard_manager.new_scorecard(..., competition_mode=True)`
- `scorecard_manager.get_scorecard(...)`

Output JSON:
```json
{
  "cards": {},
  "source_url": "https://github.com/supermodeltools/uncompact",
  "tags": [
    "supermodeltools",
    "offline"
  ],
  "opaque": {
    "benchmark": "arc-agi-3-offline-attempt"
  },
  "card_id": "6c820208-be6c-4127-b977-63068da7af54",
  "api_key": "<redacted>",
  "competition_mode": true,
  "won": 0,
  "played": 0,
  "total_actions": 0,
  "levels_completed": 0
}
```

## Final benchmark score

Because no ARC-AGI-3 environment episodes were executed in this container session, the current scorecard totals are:
- **won:** 0
- **played:** 0
- **levels_completed:** 0
- **total_actions:** 0

So the current **final benchmark score is 0 completed environments** for this run.
