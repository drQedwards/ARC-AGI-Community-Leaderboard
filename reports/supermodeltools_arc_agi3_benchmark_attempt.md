# Supermodeltools setup + full memory graph export + ARC-AGI-3 (7-game) score

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

## Full memory graph export (CLI + API attempt)

Runner:
- `scripts/export_supermodel_memory_graph.py`

Executed:
- `python scripts/export_supermodel_memory_graph.py`

Outputs:
- Full local memory/disc string: `reports/supermodel_memory_graph_full.txt`
- API attempt output file: `reports/supermodel_memory_graph_api_attempt.txt`
- Run metadata/status: `reports/supermodel_memory_graph_result.json`

Observed status:
- local CLI export: success (`return_code=0`)
- API CLI export: failed (`return_code=1`, `Forbidden` on `api.supermodeltools.com/v1/graphs/supermodel`)

## ARC-AGI-3 competition mode benchmark (all 7 games)

Runner:
- `scripts/run_arcagi3_competition_mode.py`

Executed:
- `uv run python scripts/run_arcagi3_competition_mode.py`

Target games (7):
- `ls20`, `ft09`, `bb24`, `ag06`, `hz17`, `dd33`, `rm15`

Result artifact:
- `reports/arcagi3_competition_mode_result.json`

Current ARC-AGI-3 score in this environment:
- available_environments: `0`
- scorecard_opened: `false`
- final_score_7_games:
  - games_attempted: `7`
  - games_played_successfully: `0`
  - games_failed: `7`
  - success_rate: `0.0`

Blocking cause:
- Proxy/network policy blocks `three.arcprize.org` endpoints (`/api/games`, `/api/scorecard/open`) with tunnel `403` (and one `502`) responses.

## Final score summary

- ARC-AGI-3 current score (7-game run): **0 / 7 successful**
- ARC-AGI-3 7-game success rate: **0.0**
- Supermodeltools full local memory graph string exported to `reports/supermodel_memory_graph_full.txt`
