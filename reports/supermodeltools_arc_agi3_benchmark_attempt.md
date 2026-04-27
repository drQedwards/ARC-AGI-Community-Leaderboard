# Supermodeltools setup + context bomb + scorecard + sprite-event graph

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

## Supermodeltools API attempt for graphing

Attempted API-mode graph/context request with:
- `SUPERMODEL_API_KEY=*** uncompact dry-run --mode api --max-tokens 600`

Result:
- API request failed with `Forbidden` for `https://api.supermodeltools.com/v1/graphs/supermodel`.

## Supermodeltools memory tool output (local context bomb)

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
```

## Sprite keyboard "on_click" event graph pathway (least-click path)

Because API graph endpoint was forbidden in this environment, a local graph computation was run from keyboard on-click events.

Input events file:
- `data/sprite_event_graph_example.json`

Computation:
- `python scripts/compute_sprite_event_path.py`

Output files:
- `reports/sprite_event_shortest_path.json`
- `reports/sprite_event_graph.dot`

Computed least-click path summary:
- start: `spawn`
- goal: `win`
- total_clicks: `3`
- path:
  1. `on_click:A` (`spawn -> sprite_a`)
  2. `on_click:C` (`sprite_a -> sprite_c`)
  3. `on_click:ENTER` (`sprite_c -> win`)

## Scorecard output

Opened a local competition-mode scorecard using ARC toolkit scorecard manager:
- `arc_agi.Arcade(operation_mode=OFFLINE)`
- `scorecard_manager.new_scorecard(..., competition_mode=True)`
- `scorecard_manager.get_scorecard(...)`

Output totals:
- `won`: 0
- `played`: 0
- `levels_completed`: 0
- `total_actions`: 0

## Final benchmark score for this run

- ARC scorecard in this session: **0 completed environments**.
- Sprite event least-click benchmark (local graph): **3 clicks to win**.
