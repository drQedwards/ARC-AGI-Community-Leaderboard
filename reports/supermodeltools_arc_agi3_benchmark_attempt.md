# Supermodeltools setup + LS20 listener graph benchmark

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
  - Manual install of `uncompact_linux_amd64.tar.gz` into npm package bin path.
- Status: **Completed successfully (with manual binary workaround)**.

## LS20 event-listener graph benchmark

### Listener/control source used
Direct fetch of `https://arcprize.org/tasks/ls20` is blocked in this runtime by proxy policy, so listener controls were taken from ARC preview game text (same ls20 family controls):
- Space Bar
- Click
- Undo (Z)
- Reset Level
- Help
- Start

These controls are encoded in:
- `data/ls20_listener_attempts.json`

### Benchmark objective
- Build action-chain graph attempts from listener/button events.
- Keep only the shortest complete chain to win.
- Prune incomplete attempts and any complete attempt longer than the current best.
- Attempt Supermodeltools API graph reload for LS20 and record status.

### Runner
- `scripts/benchmark_ls20_listener_graph.py`

### Output artifacts
- `reports/ls20_listener_benchmark.json`
- `reports/ls20_listener_graph.dot`

### Run result
Executed:
- `SUPERMODEL_API_KEY=*** python scripts/benchmark_ls20_listener_graph.py`

Result summary:
- attempts_total: **4**
- attempts_complete: **3**
- pruned_attempts_kept: **1**
- best_attempt: `a3`
- best_clicks: **4**

Supermodeltools API attempt:
- `api.supermodeltools.com/v1/graphs/supermodel` request attempted for `game_id=ls20`
- result: proxy tunnel `403 Forbidden` in this environment

## Additional memory-reload benchmark outputs
- `reports/sprite_event_memory_benchmark.json` (game-over recovery benchmark)
- `reports/sprite_event_shortest_path.json`
- `reports/sprite_event_graph.dot`

## Final benchmark score for this run

- **LS20 listener-chain best_clicks: 4**
- **Sprite memory-reload solved_rate: 1.0**
- **Sprite best least-click path: 3**
