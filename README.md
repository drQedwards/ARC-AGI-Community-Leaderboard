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

## Links

- [ARC Prize](https://arcprize.org)
- [ARC-AGI Benchmark](https://arcprize.org/arc-agi)
- [Community Leaderboard](https://arcprize.org/leaderboard/community)
- [Discord](https://discord.com/invite/9b77dPAmcA)
