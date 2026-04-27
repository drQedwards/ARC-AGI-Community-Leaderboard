import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.supermodeltools.com/v1/graphs/supermodel"


def make_chain_edges(chain):
    edges = []
    prev = "spawn"
    for i, action in enumerate(chain, start=1):
        node = f"s{i}"
        edges.append({"from": prev, "to": node, "event": f"on_click:{action}", "clicks": 1})
        prev = node
    edges.append({"from": prev, "to": "win", "event": "win_state", "clicks": 0})
    return edges


def to_dot(edges):
    lines = ["digraph ls20_listener_chain {", "  rankdir=LR;"]
    for e in edges:
        color = "red" if e["to"] == "win" or e["from"].startswith("s") else "black"
        lines.append(
            f'  "{e["from"]}" -> "{e["to"]}" [label="{e["event"]}/{e["clicks"]}", color={color}];'
        )
    lines.append("}")
    return "\n".join(lines)


def main():
    repo = Path(__file__).resolve().parent.parent
    data = json.loads((repo / "data" / "ls20_listener_attempts.json").read_text())

    attempts = data["attempts"]
    complete = [a for a in attempts if a["status"] == "complete"]
    best = min(complete, key=lambda a: a["clicks"]) if complete else None

    pruned = []
    for a in attempts:
        if a["status"] != "complete":
            continue
        if best and a["clicks"] > best["clicks"]:
            continue
        pruned.append(a)

    best_edges = make_chain_edges(best["chain"]) if best else []
    api_status = None
    api_key = os.getenv("SUPERMODEL_API_KEY", "")
    if api_key:
        try:
            r = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                json={"game_id": "ls20"},
                timeout=10,
            )
            api_status = f"{r.status_code} {r.text[:120]}"
        except Exception as e:
            api_status = f"error: {e}"

    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task_url": data["task_url"],
        "listener_controls": data["listener_controls"],
        "attempts_total": len(attempts),
        "attempts_complete": len(complete),
        "pruned_attempts_kept": len(pruned),
        "best_attempt": best,
        "prune_rule": "drop incomplete attempts and complete attempts with clicks > best_complete_clicks",
        "supermodel_api_graph_attempt": api_status,
        "final_score": {
            "best_clicks": best["clicks"] if best else None,
            "speed_objective": "minimize clicks",
        },
    }

    (repo / "reports" / "ls20_listener_benchmark.json").write_text(json.dumps(out, indent=2))
    (repo / "reports" / "ls20_listener_graph.dot").write_text(to_dot(best_edges))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
