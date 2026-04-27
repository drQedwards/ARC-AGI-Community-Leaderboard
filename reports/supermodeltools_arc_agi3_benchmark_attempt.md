# Supermodeltools setup + scorecard finalization
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
- Status: **Completed successfully**.

### 2) Uncompact — context recovery after compaction
- Ran:
  - `npm install -g uncompact --foreground-scripts`
- Output:
  - npm install completed, but postinstall release fetch hit `ENETUNREACH`.
- Workaround:
  - Manual install of `uncompact_linux_amd64.tar.gz` into npm package bin path.
- Status: **Completed successfully (with manual binary workaround)**.
Updated `scripts/build_scorecard_graph.py` to close scorecards after graph generation and emit closure status:
