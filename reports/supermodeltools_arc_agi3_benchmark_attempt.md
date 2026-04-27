# Supermodeltools setup + benchmark rerun + competition-mode status

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

## Fixes applied from review comments

1. Removed unconditional `requests` import in:
   - `scripts/benchmark_sprite_event_memory.py`
   - `scripts/benchmark_ls20_listener_graph.py`
2. Both scripts now run local-only paths even when `requests` is not installed.
3. Replaced binary submission artifact:
   - removed `submissions/scorecard_graph.parquet`
   - added text artifact `submissions/scorecard_graph.csv`

## Benchmarks re-run

Executed:
- `python scripts/benchmark_sprite_event_memory.py`
- `python scripts/benchmark_ls20_listener_graph.py`
- `python scripts/compute_sprite_event_path.py`
- `python scripts/build_scorecard_graph.py`
- `uv run python scripts/run_arcagi3_competition_mode.py`

Outputs refreshed:
- `reports/sprite_event_memory_benchmark.json`
- `reports/ls20_listener_benchmark.json`
- `reports/sprite_event_shortest_path.json`
- `reports/scorecard_graph.json`
- `reports/arcagi3_competition_mode_result.json`
- `submissions/scorecard_graph.csv`

## Competition-mode rerun result

- mode: `competition`
- available_environments: `0`
- `ls20` / `ft09` attempts: failed
- scorecard_opened: `false`
- status: `blocked_opening_scorecard`

Blocking cause remains environment network policy:
- proxy tunnel `403 Forbidden` for `three.arcprize.org` endpoints (`/api/games`, `/api/scorecard/open`).

## Final benchmark summary for this rerun

- LS20 listener-chain best_clicks: **4**
- Sprite shortest path best_clicks: **3**
- Sprite memory-reload solved_rate: **1.0**
- Competition-mode full ARC-AGI-3 benchmark: **blocked by proxy 403**
