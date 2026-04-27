import json
import heapq
from pathlib import Path


def shortest_path(start, goal, edges):
    graph = {}
    for e in edges:
        graph.setdefault(e['from'], []).append(e)

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
            heapq.heappush(
                pq,
                (cost + int(e.get('clicks', 1)), seq, e['to'], path + [e]),
            )
    return None, []


def to_dot(edges, best_edges):
    best = {(e['from'], e['to'], e['event']) for e in best_edges}
    lines = ["digraph sprite_events {", "  rankdir=LR;"]
    for e in edges:
        key = (e['from'], e['to'], e['event'])
        color = "red" if key in best else "gray"
        pen = "3" if key in best else "1"
        label = f"{e['event']} / {e.get('clicks', 1)}"
        lines.append(
            f'  "{e["from"]}" -> "{e["to"]}" [label="{label}", color={color}, penwidth={pen}];'
        )
    lines.append("}")
    return "\n".join(lines)


def main():
    repo = Path(__file__).resolve().parent.parent
    inp = repo / "data" / "sprite_event_graph_example.json"
    out_json = repo / "reports" / "sprite_event_shortest_path.json"
    out_dot = repo / "reports" / "sprite_event_graph.dot"

    data = json.loads(inp.read_text())
    total_clicks, best_path = shortest_path(data['start'], data['goal'], data['edges'])

    result = {
        "start": data['start'],
        "goal": data['goal'],
        "total_clicks": total_clicks,
        "path": best_path,
    }
    out_json.write_text(json.dumps(result, indent=2))
    out_dot.write_text(to_dot(data['edges'], best_path))

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
