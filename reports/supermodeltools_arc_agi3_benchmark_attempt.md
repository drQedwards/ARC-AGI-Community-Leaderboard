# Supermodeltools setup + scorecard finalization

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
- Status: **Completed successfully**.

### 2) Uncompact — context recovery after compaction
- Ran:
  - `npm install -g uncompact --foreground-scripts`
- Output:
  - npm install completed, but postinstall release fetch hit `ENETUNREACH`.
- Workaround:
  - Manual install of `uncompact_linux_amd64.tar.gz` into npm package bin path.
- Status: **Completed successfully (with manual binary workaround)**.

## Scorecard finalization requested

Updated `scripts/build_scorecard_graph.py` to close scorecards after graph generation and emit closure status:
- closes each created scorecard via `ScorecardManager.close_scorecard(...)`
- writes `reports/scorecard_closure_result.json`
- includes final score value for easy retrieval

Executed:
- `python scripts/build_scorecard_graph.py`

## Final score card score

From `reports/scorecard_closure_result.json`:
- `final_scorecard_score`: **1.0**
- `final_scorecard_best_clicks`: **3**
- `final_scorecard_id`: `fe8e5217-cb6a-4293-9b1e-bb1c37b8670f`

## Scorecard close-out result

All generated scorecards were closed in this run:
- `cb4aa70f-c1dc-4cc6-83c8-a24d2d62a0e2` → closed: true
- `11054be3-807c-4483-b8a5-39d566d293d3` → closed: true
- `fe8e5217-cb6a-4293-9b1e-bb1c37b8670f` → closed: true

Closure metadata is recorded in:
- `reports/scorecard_closure_result.json`
