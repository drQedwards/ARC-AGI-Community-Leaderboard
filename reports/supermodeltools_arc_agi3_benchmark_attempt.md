# Supermodeltools setup + sprite memory-reload benchmark

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
- Verification:
  - `uncompact dry-run --mode local --max-tokens 300`
- Status: **Completed successfully (with manual binary workaround)**.

## Benchmark: sprite event graph reload after game-over

Goal:
- Benchmark the workflow where a `game_over` event triggers graph reload from Supermodeltools API, then falls back to prior memory graph if needed.

### Benchmark inputs/code
- Dataset: `data/sprite_event_benchmark_cases.json`
- Runner: `scripts/benchmark_sprite_event_memory.py`

### What the benchmark does
1. Computes least-click path per episode.
2. On `game_over`, tries Supermodeltools API graph reload (`/v1/graphs/supermodel`).
3. If API reload fails, reloads prior successful graph from local memory cache.
4. Produces a benchmark JSON with solved-rate/click metrics.

### Run result
Executed with API key set:
- `SUPERMODEL_API_KEY=*** python scripts/benchmark_sprite_event_memory.py`

Result summary:
- episodes_total: **3**
- episodes_with_path: **3**
- memory_recoveries: **1**
- avg_clicks_on_solved: **3.0**
- final solved_rate: **1.0**
- least_clicks_best_episode: **3**

API call status during game-over recovery:
- API attempt returned proxy-tunnel `403 Forbidden` for `api.supermodeltools.com`
- Recovery succeeded via local memory graph reload.

## Output artifacts
- `reports/sprite_event_memory_benchmark.json` (benchmark output)
- `reports/sprite_event_shortest_path.json` (least-click path)
- `reports/sprite_event_graph.dot` (graphviz representation)

## Final benchmark score for this run

- **Sprite memory-reload solved_rate: 1.0**
- **Best least-click path: 3 clicks**
- **Average clicks on solved episodes: 3.0**
