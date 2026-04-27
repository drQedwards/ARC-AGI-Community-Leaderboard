import json
import heapq
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.supermodeltools.com/v1/graphs/supermodel"


def shortest_path(start, goal, edges):
    graph = {}
    for e in edges:
        graph.setdefault(e["from"], []).append(e)

    seq = 0
    pq = [(0, seq, start, [])]
    seen = {}

    while pq:
        cost, _, node, path = heapq.heappop(pq)
        if node in seen and seen[node] <= cost:
            continue
        seen[node] = cost
        if node == goal:
            return cost, path
        for e in graph.get(node, []):
            seq += 1
            heapq.heappush(pq, (cost + int(e.get("clicks", 1)), seq, e["to"], path + [e]))
    return None, []


def try_load_graph_from_supermodel_api(game_id: str, api_key: str):
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    payload = {"game_id": game_id}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "edges" in data:
                return data, None
        return None, f"{r.status_code} {r.text[:120]}"
    except Exception as e:
        return None, str(e)


def main():
    repo = Path(__file__).resolve().parent.parent
    cases = json.loads((repo / "data" / "sprite_event_benchmark_cases.json").read_text())

    api_key = os.getenv("SUPERMODEL_API_KEY", "")
    game_id = cases["game_id"]
    episodes = cases["episodes"]

    memory_cache = {}
    results = []
    api_attempts = []

    for ep in episodes:
        ep_edges = ep["edges"]
        clicks, path = shortest_path(ep["start"], ep["goal"], ep_edges)

        if ep["outcome"] == "win" and clicks is not None:
            memory_cache[game_id] = {"edges": ep_edges, "path": path, "clicks": clicks}
            results.append({"episode": ep["id"], "status": "win", "clicks": clicks, "used_memory_reload": False})
            continue

        # game_over: try API reload first, then local memory fallback
        used_memory_reload = False
        api_status = None
        if api_key:
            api_graph, api_err = try_load_graph_from_supermodel_api(game_id, api_key)
            api_status = "ok" if api_graph else f"error: {api_err}"
            api_attempts.append({"episode": ep["id"], "status": api_status})
            if api_graph and "edges" in api_graph:
                clicks2, path2 = shortest_path(ep["start"], ep["goal"], api_graph["edges"])
                if clicks2 is not None:
                    used_memory_reload = True
                    memory_cache[game_id] = {"edges": api_graph["edges"], "path": path2, "clicks": clicks2}
                    results.append({"episode": ep["id"], "status": "recovered_via_api", "clicks": clicks2, "used_memory_reload": True})
                    continue

        # local fallback memory graph
        if game_id in memory_cache:
            old = memory_cache[game_id]
            clicks3, path3 = shortest_path(ep["start"], ep["goal"], old["edges"])
            if clicks3 is not None:
                used_memory_reload = True
                results.append({"episode": ep["id"], "status": "recovered_via_local_memory", "clicks": clicks3, "used_memory_reload": True})
                continue

        results.append({"episode": ep["id"], "status": "game_over_unrecovered", "clicks": None, "used_memory_reload": used_memory_reload})

    wins = [r for r in results if r["clicks"] is not None]
    avg_clicks = round(sum(r["clicks"] for r in wins) / len(wins), 3) if wins else None

    benchmark = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "game_id": game_id,
        "episodes_total": len(episodes),
        "episodes_with_path": len(wins),
        "memory_recoveries": sum(1 for r in results if r["used_memory_reload"]),
        "avg_clicks_on_solved": avg_clicks,
        "results": results,
        "supermodel_api_attempts": api_attempts,
        "final_score": {
            "solved_rate": round(len(wins) / len(episodes), 3),
            "least_clicks_best_episode": min((r["clicks"] for r in wins), default=None),
            "avg_clicks_on_solved": avg_clicks,
        },
    }

    out = repo / "reports" / "sprite_event_memory_benchmark.json"
    out.write_text(json.dumps(benchmark, indent=2))
    print(json.dumps(benchmark, indent=2))


if __name__ == "__main__":
    main()
