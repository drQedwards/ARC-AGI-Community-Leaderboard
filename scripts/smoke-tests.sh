#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python scripts/benchmark_sprite_event_memory.py
python scripts/run_arcagi3_competition_mode.py
