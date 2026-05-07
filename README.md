# ARC Prize Community Leaderboard

A community-driven showcase of ARC-AGI methods, harnesses, and approaches for [ARC-AGI](https://arcprize.org). Open to anyone - submit via Pull Request.

> **Note:** Scores are self-reported and have not been verified by ARC Prize. ARC Prize may choose to verify submissions at its discretion. For verified scores, see the [official leaderboard](https://arcprize.org/leaderboard).

## How to Submit

1. Fork this repository
2. Copy `submissions/.example/` to `submissions/<your-submission-id>/`
   - Use a short, lowercase, hyphenated ID (e.g. `my-harness-v2`)
3. Fill in `submission.yaml` following the template
4. Open a Pull Request


A maintainer reviews and merges submissions on a weekly basis.

Submissions must link to a publicly accessible code repository and report a score on the **public** set of one or more benchmarks. For ARC-AGI-3, submissions must use [Competition Mode](https://docs.arcprize.org/toolkit/competition_mode) and provide a `scorecard_url`. See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.


## Script Environment Variables

Some helper scripts in `scripts/` require API keys to be provided via environment variables (no hardcoded secrets):

- `scripts/export_supermodel_memory_graph.py` requires `SUPERMODEL_API_KEY`
- `scripts/run_arcagi3_competition_mode.py` requires `ARC_API_KEY`

Example:

```bash
export SUPERMODEL_API_KEY="<your-supermodel-api-key>"
export ARC_API_KEY="<your-arc-api-key>"
python scripts/export_supermodel_memory_graph.py
python scripts/run_arcagi3_competition_mode.py
```

If a required variable is missing, each script writes a JSON result with `status: "missing_env_var"` and a clear message.


### Scorecard graph utilities

Use `scripts/rewind_scorecard_graph.py` to fetch a local or HTTP(S) scorecard graph artifact, validate its node/edge references, write a normalized copy, and emit a rewound graph with reversed node order and edge direction:

```bash
python scripts/rewind_scorecard_graph.py
python scripts/rewind_scorecard_graph.py --source https://example.com/scorecard_graph.json
```


### Transaction history utilities

Use `scripts/rewind_transaction_history.py` to fetch Solana transaction signatures from a local fixture, HTTP(S) JSON artifact, or live RPC address, validate the history, write a normalized copy, and emit an oldest-first rewound history:

```bash
python scripts/rewind_transaction_history.py
python scripts/rewind_transaction_history.py --address B4cd9KaWdk6vqCxE9WRv3WVmZv26joZfQyG7q57xpump --limit 25
```


### Solana address state proof

Use `scripts/inspect_solana_address_state.py` from a backend/cloud terminal to query the current Solana account state for the configured agent token mint (or any supplied address) via JSON-RPC. The script records either the live account/token state or a structured `fetch_failed` report if RPC egress is blocked:

```bash
python scripts/inspect_solana_address_state.py
python scripts/inspect_solana_address_state.py --address B4cd9KaWdk6vqCxE9WRv3WVmZv26joZfQyG7q57xpump --rpc-url "$SOLANA_RPC_URL"
```

### Model slug notes

Do not invent a future model slug in this repo. A model slug is an API-facing identifier string, not proof that a model exists. Treat examples such as `gpt-5.5`, `gpt-5.5-2026-05-07`, or a hypothetical `gpt-6-*` as illustrative naming shapes only unless they appear in the provider's live model list or official documentation.

For backend agents, record the runtime model identity separately from Solana token identity:

- Model slug: the AI model identifier selected by the API/runtime.
- Agent token mint: the Solana mint address configured by `AGENT_TOKEN_MINT_ADDRESS`.
- Current token state: fetched from Solana RPC with `scripts/inspect_solana_address_state.py`; if RPC egress is blocked, keep the structured `fetch_failed` report instead of guessing.

Goblin rule: if the goblin claims to be `gpt-6`, make it show the model-list entry or official docs; if the goblin claims a contract address exists, make it show the Solana RPC account state.


## Links

- [ARC Prize](https://arcprize.org)
- [ARC-AGI Benchmark](https://arcprize.org/arc-agi)
- [Community Leaderboard](https://arcprize.org/leaderboard/community)
- [Discord](https://discord.com/invite/9b77dPAmcA)
